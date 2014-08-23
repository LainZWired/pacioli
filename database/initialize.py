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

import uuid
import api

def initialize_general_journal():
  space_name = "GeneralJournal"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'GeneralJournal',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  print(api.add_record(space_configuration))

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Date',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Debits',
    'typeofattribute': 'set(string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'GeneralJournal',
    'nameofattribute': 'Credits',
    'typeofattribute': 'set(string)',
    'insubspace': False}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    print(api.add_record(attribute))

  print(api.add_space(space_name))

def initialize_general_ledger():
  space_name = "GeneralLedger"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'GeneralLedger',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  print(api.add_record(space_configuration))

  space_attributes = [\
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

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    print(api.add_record(attribute))

  print(api.add_space(space_name))



if __name__ == '__main__':
  api.reset_system()
  initialize_general_journal()
  initialize_general_ledger()
