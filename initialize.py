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

def initialize_memoranda():
  space_name = "Memoranda"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'Memoranda',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'Date',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'Filename',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'Filetype',
    'typeofattribute': 'string',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'Filesize',
    'typeofattribute': 'string',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'File',
    'typeofattribute': 'string',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'FileMapName',
    'typeofattribute': 'string',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'Memoranda',
    'nameofattribute': 'TransactionUniques',
    'typeofattribute': 'set(string)',
    'insubspace': False}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)


def initialize_memoranda_transactions():
  space_name = "MemorandaTransactions"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'MemorandaTransactions',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'MemorandaTransactions',
    'nameofattribute': 'MemorandaUnique',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'MemorandaTransactions',
    'nameofattribute': 'Details',
    'typeofattribute': 'map(string, string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'MemorandaTransactions',
    'nameofattribute': 'TransactionMapName',
    'typeofattribute': 'string',
    'insubspace': False}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)



def initialize_filemaps():
  space_name = "FileMaps"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'FileMaps',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMaps',
    'nameofattribute': 'FileMapName',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMaps',
    'nameofattribute': 'FileMappingUniques',
    'typeofattribute': 'set(string)',
    'insubspace': False}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)

def initialize_filemappings():
  space_name = "FileMappings"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'FileMappings',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMappings',
    'nameofattribute': 'FileMapName',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMappings',
    'nameofattribute': 'FileMappingName',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMappings',
    'nameofattribute': 'FileMapping',
    'typeofattribute': 'map(string, string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'FileMappings',
    'nameofattribute': 'TransactionKey',
    'typeofattribute': 'string',
    'insubspace': True}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)



def initialize_transactionmaps():
  space_name = "TransactionMaps"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'TransactionMaps',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)


  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMaps',
    'nameofattribute': 'TransactionMapName',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMaps',
    'nameofattribute': 'TransactionMappingUniques',
    'typeofattribute': 'set(string)',
    'insubspace': False}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)

def initialize_transactionmappings():
  space_name = "TransactionMappings"
  unique = uuid.uuid4()
  unique = str(unique)
  space_configuration = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'TransactionMappings',
    'keyname':'unique',
    'partitioncount':'8',
    'failurecount':'2'}
  api.add_record(space_configuration)

  space_attributes = [\
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMappings',
    'nameofattribute': 'TransactionMapName',
    'typeofattribute': 'string',
    'insubspace': True},
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMappings',
    'nameofattribute': 'TransactionMappingName',
    'typeofattribute': 'map(string, string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMapping',
    'nameofattribute': 'Map',
    'typeofattribute': 'map(string, string)',
    'insubspace': False},
    {'entry_space':'spaceattributes',
    'nameofspace': 'TransactionMappings',
    'nameofattribute': 'LedgerKey',
    'typeofattribute': 'string',
    'insubspace': True}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)


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
  api.add_record(space_configuration)

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
    api.add_record(attribute)

  api.add_space(space_name)

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
  api.add_record(space_configuration)

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
    'nameofattribute': 'gjUnique',
    'typeofattribute': 'string',
    'insubspace': True}]

  for attribute in space_attributes:
    unique = uuid.uuid4()
    unique = str(unique)
    attribute['unique']=unique
    api.add_record(attribute)

  api.add_space(space_name)



if __name__ == '__main__':
  api.reset_system()
  initialize_memoranda()
  initialize_memoranda_transactions()
  initialize_filemaps()
  initialize_filemappings()
  initialize_transactionmaps()
  initialize_transactionmappings()
  initialize_general_journal()
  initialize_general_ledger()
