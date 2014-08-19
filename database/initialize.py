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
import uuid

def start_system():
  start = post('http://192.168.59.103:4000/system', data={'command':'start'}).json()

def reset_system():
  reset = post('http://192.168.59.103:4000/system', data={'command':'reset'}).json()

def stop_system():
  reset = post('http://192.168.59.103:4000/system', data={'command':'stop'}).json()

def initialize_general_journal():
  unique = uuid.uuid4()
  unique = str(unique)
  spacemap_data = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'GeneralJournal',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  spacemap_entry = post('http://192.168.59.103:4000/entries', data=spacemap_data).json()
  print(spacemap_entry)

  spaceattributes_data = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Date',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Debits',
    'typeofattribute': 'list(string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Credits',
    'typeofattribute': 'list(string)',
    'insubspace': False}]

  for attribute in spaceattributes_data:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    spaceattributes_entry = post('http://192.168.59.103:4000/entries', data=attribute).json()
    print(spaceattributes_entry)


  space_create = post('http://192.168.59.103:4000/space', data={'entry_space':'GeneralJournal'}).json()
  print(space_create)

def initialize_general_ledger():
  unique = uuid.uuid4()
  unique = str(unique)
  spacemap_data = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'GeneralLedger',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  spacemap_entry = post('http://192.168.59.103:4000/entries', data=spacemap_data).json()
  print(spacemap_entry)


  spaceattributes_data = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'Date',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'Type',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'Account',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'Amount',
    'typeofattribute': 'int',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'Unit',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralLedger',
    'nameofattribute': 'gjUUID',
    'typeofattribute': 'string',
    'insubspace': True}]

  for attribute in spaceattributes_data:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    spaceattributes_entry = post('http://192.168.59.103:4000/entries', data=attribute).json()
    print(spaceattributes_entry)
  space_create = post('http://192.168.59.103:4000/space', data={'entry_space':'GeneralLedger'}).json()
  print(space_create)


if __name__ == '__main__':
  reset_system()
  initialize_general_journal()
  initialize_general_ledger()
