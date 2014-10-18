#!venv/bin/python

from pacioli import db

db.drop_all()
db.create_all()
