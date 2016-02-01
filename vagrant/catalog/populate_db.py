from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from create_db import Category, Item, Base

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# delete all existing entries
session.query(Item).delete()
session.query(Category).delete()
session.commit()

# Categories for items
basketball = Category(name = "Basketball")
session.add(basketball)

basketballItem1 = Item(name = "Basketball Shoes", \
	description = "Shoes for basketball", category = basketball)
session.add(basketballItem1)

basketballItem2 = Item(name = "Basketball", \
	description = "Ball for basketball", category = basketball)
session.add(basketballItem2)

tennis = Category(name = "Tennis")
session.add(tennis)

tennisItem1 = Item(name = "Tennis Racket", \
	description = "Racket for tennis", category = tennis)
session.add(tennisItem1)

surfing = Category(name = "Surfing")
session.add(surfing)

scubaDiving = Category(name = "Scuba Diving")
session.add(scubaDiving)
session.commit()

print "Added 4 categories, with 2, 1, 0, 0 each!"
