from flask import Flask, render_template, jsonify, request, redirect, url_for, session as login_session, make_response, flash
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from create_db import Base, Category, Item
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string

app = Flask(__name__)

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
					for x in xrange(32))
	login_session['state'] = state
	print "The current session state is %s" % login_session['state']
	return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
	print 'server side gconnect'
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
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
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

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'),
								 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# See if a user exists, if it doesn't make a new one

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output

# Show all categories
@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def ShowAllCategories():
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
	print item_name
	item = session.query(Item).filter_by(name=item_name).one()
	return render_template('item.html', item=item, category=category)

# CRUD functions
@app.route("/catalog/<item_name>/delete", methods=['GET', 'POST'])
def deleteItem(item_name):
	if 'username' not in login_session:
		return redirect('/login')
	itemToDelete = session.query(Item).filter_by(name=item_name).one()
	if request.method == 'POST':
		category_name = itemToDelete.category.name
		session.delete(itemToDelete)
		session.commit()
		return redirect(url_for('category', category_name=category_name))
	else:
		return render_template('deleteItem.html', item=itemToDelete)

@app.route("/catalog/<category_name>/new", methods=['GET', 'POST'])
def newItem(category_name):
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		category = session.query(Category).filter_by(name=request.form['category_name']).one()
		newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category.id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('item', category_name=request.form['category_name'], item_name=newItem.name))
	else:
		categories = session.query(Category)
		return render_template('newItem.html', category_name=category_name, categories=categories)

@app.route("/catalog/<item_name>/edit", methods=['GET', 'POST'])
def updateItem(item_name):
	if 'username' not in login_session:
		return redirect('/login')
	editItem = session.query(Item).filter_by(name=item_name).one()
	if request.method == 'POST':
		if request.form['name']:
			editItem.name = request.form['name']
		if request.form['description']:
			editItem.description = request.form['description']
		if request.form['category_name']:
			category = session.query(Category).filter_by(name=request.form['category_name']).one()
			editItem.category = category
			editItem.category_id = category.id
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


# if run as a main function
if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='localhost', port=9000)