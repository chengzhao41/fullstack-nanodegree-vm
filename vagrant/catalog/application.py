from flask import Flask, render_template, jsonify
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
	category = session.query(Category).filter_by(name=category_name).one()
	item = session.query(Item).filter_by(name=item_name).one()
	return render_template('item.html', item=item, category=category)

# CRUD functions
@app.route("/catalog/<category_name>/edit")
@app.route("/catalog/<category_name>/delete")
@app.route("/catalog/<category_name>/new")
@app.route("/catalog/<category_name>/update")

# JSON ENDPOINT
@app.route('/catalog.json')
def categoryJSON():
	categories = session.query(Category)
	return jsonify(Category = [c.serialize for c in categories])

@app.route('/catalog/<category_name>/<item_name>.json')
def itemJSON(item_id):
	categories = session.query(Category)
	return jsonify(Category = [c.serialize for c in categories])


# if run as a main function
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=000)