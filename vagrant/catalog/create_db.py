import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine, TIMESTAMP, func

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(50), nullable=False)
	picture = Column(String(250))

class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	last_modified_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
	items = relationship("Item", single_parent=True)
	
	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'id': self.id,
			'name': self.name,
			'items': [i.serialize for i in self.items],
			'last_modified_time': self.last_modified_time.strftime("%a, %d %b %Y %H:%M:%S")
		}

class Item(Base):
	__tablename__ = 'item'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	description = Column(String(250))
	picture = Column(String(250))
	last_modified_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())
	category_id = Column(Integer, ForeignKey('category.id'))
	user_id = Column(Integer, ForeignKey('user.id'))
	category = relationship(Category)
	user = relationship(User)

	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'id': self.id,
			'name': self.name,
			'description': self.description,
			'picture': self.picture,
			'category_id': self.category_id,
			'user_id': self.user_id,
			'last_modified_time': self.last_modified_time.strftime("%a, %d %b %Y %H:%M:%S")
		}

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)