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

from requests import put, get, post
from config import *

address = DATABASE_ADDRESS + ":" + str(DATABASE_PORT) + "/"

def start_system():
  return post(address + 'system', data={'command':'start'}).json()

def reset_system():
  return post(address + 'system', data={'command':'reset'}).json()

def stop_system():
  return post(address + 'system', data={'command':'stop'}).json()

def add_space(name):
  return post(address + 'space', data={'entry_space':name}).json()

def add_record(record):
  return post(address + 'entries', data=record).json()
