from flask import Flask, render_template, jsonify, request, redirect, url_for
app = Flask(__name__)

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from create_db import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

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
	app.debug = True
	app.run(host='0.0.0.0', port=9000)