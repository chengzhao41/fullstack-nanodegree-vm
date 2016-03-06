from flask import Flask, render_template, jsonify, request, redirect, url_for, \
session as login_session, make_response, flash, send_from_directory, safe_join

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from create_db import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from werkzeug import secure_filename
from flask.ext.seasurf import SeaSurf
from werkzeug.contrib.atom import AtomFeed
from urlparse import urljoin
from functools import wraps

import httplib2
import json
import requests
import random
import string
import os

app = Flask(__name__, static_url_path = "/images", static_folder = "images")
csrf = SeaSurf(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
UPLOAD_FOLDER = '/Users/chengzhao/Git/fullstack-nanodegree-vm/vagrant/catalog/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# decorator
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' in login_session:
			return f(*args, **kwargs)
		else:
			return redirect(url_for('showLogin', next=request.url))
	return decorated_function

# Create anti-forgery state token
@csrf.exempt
@app.route('/login')
def showLogin():
	# clearing the login session just in case
	login_session.clear()
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
					for x in xrange(32))
	login_session['state'] = state
	print login_session
	return render_template('login.html', STATE=state)

@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		print 'invalid state token'
		return response
	# Obtain authorization code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		print 'flow exception'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		   % access_token)
	print url
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id
	# ADD PROVIDER TO LOGIN SESSION
	login_session['provider'] = 'google'

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)
	data = answer.json()
	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# See if a user exists, if it doesn't make a new one
	# Update user if it does, in case name or picture changed
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
		login_session['user_id'] = user_id
	else:
		login_session['user_id'] = user_id
		updateUser(login_session)

	print "End of gconnect"
	print login_session

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	return output

@app.route('/gdisconnect')
def gdisconnect():
	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(
			json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials.access_token
	print access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	if result['status'] != '200':
		# For whatever reason, the given token was invalid.
		response = make_response(
			json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response

@csrf.exempt
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = request.data
	print "access token received %s " % access_token

	app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
		'web']['app_id']
	app_secret = json.loads(
		open('fb_client_secrets.json', 'r').read())['web']['app_secret']
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
		app_id, app_secret, access_token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# Use token to get user info from API
	userinfo_url = "https://graph.facebook.com/v2.4/me"
	# strip expire tag from access token
	token = result.split("&")[0]

	url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	print "url sent for API access:%s"% url
	print "API JSON result: %s" % result
	data = json.loads(result)
	login_session['provider'] = 'facebook'
	login_session['username'] = data["name"]
	login_session['email'] = data["email"]
	login_session['facebook_id'] = data["id"]

	# The token must be stored in the login_session in order to properly logout, 
	# let's strip out the information before the equals sign in our token
	stored_token = token.split("=")[1]
	login_session['access_token'] = stored_token

	# Get user picture
	url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)

	login_session['picture'] = data["data"]["url"]

	# See if a user exists, if it doesn't make a new one
	# Update user if it does, in case name or picture changed
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
		login_session['user_id'] = user_id
	else:
		login_session['user_id'] = user_id
		updateUser(login_session)

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']

	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

	flash("Now logged in as %s" % login_session['username'])

	print "End of fbconnect"
	print login_session
	
	return output

@app.route('/fbdisconnect')
def fbdisconnect():
	if 'facebook_id' in login_session and 'access_token' in login_session:
		facebook_id = login_session['facebook_id']
		# The access token must me included to successfully logout
		access_token = login_session['access_token']
		url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
		h = httplib2.Http()
		result = h.request(url, 'DELETE')[1]
		return "you have been logged out"
	else:
		return "no fb access_token found"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
	if 'provider' in login_session:
		print login_session['provider']
		if login_session['provider'] == 'google':
			gdisconnect()
			del login_session['gplus_id']
			del login_session['credentials']
		if login_session['provider'] == 'facebook':
			fbdisconnect()
			del login_session['facebook_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['user_id']
		del login_session['provider']
		flash("You have successfully been logged out.")
		return redirect(url_for('showAllCategories'))
	else:
		print "no provider"
		# clearing the login session just in case
		login_session.clear()
		flash("You were not logged in")
		return redirect(url_for('showAllCategories'))

# Show all categories
@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def showAllCategories():
	print login_session
	categories = session.query(Category)
	items = session.query(Item)
	return render_template(\
		'main.html', categories=categories, items=items)

@app.route('/catalog/<category_name>')
@app.route('/catalog/<category_name>/')
@app.route('/catalog/<category_name>/Items')
@app.route('/catalog/<category_name>/Items/')
def category(category_name):
	category = session.query(Category).filter_by(name=category_name).one()
	items = session.query(Item).filter_by(category_id=category.id)
	return render_template(\
		'catalog.html', category=category, items=items)

@app.route('/catalog/<category_name>/<item_name>')
@app.route('/catalog/<category_name>/<item_name>/')
def item(category_name, item_name):
	item = session.query(Item).filter_by(name=item_name).one()
	if item.picture is None:
		filename = None
	else:
		filename = str(item.user_id) + "_" + item.picture
		print filename
	if 'user_id' not in login_session or item.user_id != login_session['user_id']:
		print 'public item!'
		return render_template('publicItem.html', item=item, category=category, filename = filename)
	else:
		print 'user item!'
		return render_template('item.html', item=item, category=category, filename = filename)

# CRUD functions
@app.route("/catalog/<item_name>/delete", methods=['GET', 'POST'])
@login_required
def deleteItem(item_name):
	itemToDelete = session.query(Item).filter_by(name=item_name).one()
	if login_session['user_id'] != itemToDelete.user_id:
		return "<script>function myFunction() {alert('You are not authorized to delete this item, as it is not yours.');}</script>" \
		+ "<body onload='myFunction()''>"
	if request.method == 'POST':
		category_name = itemToDelete.category.name
		# delete file if it exists
		if (itemToDelete.picture is not None and os.path.isfile(safe_join(app.config['UPLOAD_FOLDER'], str(itemToDelete.user_id) + "_" + itemToDelete.picture))):
			os.remove(safe_join(app.config['UPLOAD_FOLDER'], str(itemToDelete.user_id) + "_" + itemToDelete.picture))
		session.delete(itemToDelete)
		session.commit()
		return redirect(url_for('category', category_name=category_name))
	else:
		return render_template('deleteItem.html', item=itemToDelete)

@app.route("/catalog/<category_name>/new", methods=['GET', 'POST'])
@login_required
def newItem(category_name):
	if request.method == 'POST':
		file = request.files['file']
		if file and allowed_file(file.filename):
			print 'saving files...'
			filename = secure_filename(file.filename)
			file.save(safe_join(app.config['UPLOAD_FOLDER'], str(getUserID(login_session['email'])) + "_" + filename))
			print 'saved file!'
			
		category = session.query(Category).filter_by(name=request.form['category_name']).one()
		try:
			filename
		except NameError:
			newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category.id, \
				user_id=getUserID(login_session['email']))
		else:			
			newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category.id, \
				user_id=getUserID(login_session['email']), picture=filename)
		session.add(newItem)
		session.commit()
		return redirect(url_for('item', category_name=request.form['category_name'], item_name=newItem.name))
	else:
		categories = session.query(Category)
		return render_template('newItem.html', category_name=category_name, categories=categories)

@app.route("/catalog/<item_name>/edit", methods=['GET', 'POST'])
@login_required
def updateItem(item_name):
	editItem = session.query(Item).filter_by(name=item_name).one()
	if login_session['user_id'] != editItem.user_id:
		return "<script>function myFunction() {alert('You are not authorized to edit this item, as it is not yours.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		if request.form['name']:
			editItem.name = request.form['name']
		if request.form['description']:
			editItem.description = request.form['description']
		if request.form['category_name']:
			category = session.query(Category).filter_by(name=request.form['category_name']).one()
			editItem.category = category
			editItem.category_id = category.id
		file = request.files['file']
		if file and allowed_file(file.filename):
			print 'updating files...'
			filename = secure_filename(file.filename)

			# delete old file if it exists
			if (os.path.isfile(safe_join(app.config['UPLOAD_FOLDER'], str(editItem.user_id) + "_" + editItem.picture))):
				print 'deleting old file...'
				os.remove(safe_join(app.config['UPLOAD_FOLDER'], str(editItem.user_id) + "_" + editItem.picture))
			# save new file
			file.save(safe_join(app.config['UPLOAD_FOLDER'], str(editItem.user_id) + "_" + filename))
			editItem.picture = filename
			print 'updated file!'

		session.add(editItem)
		session.commit()
		return redirect(url_for('item', category_name=request.form['category_name'], item_name=editItem.name))
	else:
		categories = session.query(Category)
		return render_template('updateItem.html', item=editItem, categories=categories)

# JSON ENDPOINT
@app.route('/catalog.json')
def catalogJSON():
	categories = session.query(Category)
	return jsonify(Category = [c.serialize for c in categories])

@app.route('/catalog/<category_name>.json')
def categoryJSON(category_name):
	category = session.query(Category).filter_by(name=category_name).one()
	return jsonify(Category = category.serialize)

@app.route('/catalog/<category_name>/<item_name>.json')
def itemJSON(category_name, item_name):
	item = session.query(Item).filter_by(name=item_name).one()
	return jsonify(Item = item.serialize)

# Atom
def make_external(url):
	return urljoin(request.url_root, url)

@app.route('/catalog.atom')
def catalogAtom():
	feed = AtomFeed('Recent Categories',
					feed_url=request.url, url=request.url_root)
	categories = session.query(Category).order_by(Category.last_modified_time.desc()).limit(15).all()
	for category in categories:
		feed.add(category.name, unicode(category.name),
				 content_type='html',
				 url=make_external(category.name),
				 updated=category.last_modified_time)
	return feed.get_response()

@app.route('/catalog/<category_name>.atom')
def itemAtom(category_name):
	feed = AtomFeed('Recent Items in ' + category_name,
					feed_url=request.url, url=request.url_root)
	items = session.query(Item).join(Category).filter(Category.name==category_name).order_by(Item.last_modified_time.desc()).limit(15).all()
	for item in items:
		feed.add(item.name, unicode(item.description),
				 content_type='html',
				 url=make_external('/catalog/' + category_name + '/' + item.name),
				 updated=item.last_modified_time)
	return feed.get_response()

# User Helper Functions
def createUser(login_session):
	newUser = User(name=login_session['username'], email=login_session[
				   'email'], picture=login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id

def updateUser(login_session):
	user = session.query(User).filter_by(id=login_session['user_id']).one()
	user.name = login_session['username']
	user.picture = login_session['picture']
	session.add(user)
	session.commit()

def getUser(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user

def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

# upload functions
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# if run as a main function
if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='localhost', port=9000)