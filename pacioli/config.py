# -*- coding: utf8 -*-

# Copyright (c) 2014, Satoshi Nakamoto Institute
# All rights reserved.
#
# This file is part of Pacioli.
#
# Pacioli is free software: you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pacioli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pacioli.  If not, see <http://www.gnu.org/licenses/>.

# The CSRF_ENABLED setting activates the cross-site request forgery prevention. 
# In most cases you want to have this option enabled as it makes your app more secure.


CSRF_ENABLED = True

# Change the secret key. 

SECRET_KEY = 'eaoR2CMuUKp1'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf','tiff', 'xlsx','xls','csv'])
SQLALCHEMY_DATABASE_URI = "postgresql://pacioli@localhost/pacioli"
