# -*- coding: utf8 -*-

# The CSRF_ENABLED setting activates the cross-site request forgery prevention. 
# In most cases you want to have this option enabled as it makes your app more secure.


CSRF_ENABLED = True

# Change the secret key. 

SECRET_KEY = 'eaoR2CMuUKp1'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf','tiff', 'xlsx','xls','csv'])
SQLALCHEMY_DATABASE_URI = "postgresql://bitstein@localhost/pacioli"
