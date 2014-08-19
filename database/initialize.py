from requests import put, get,post
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
    'partitioncount':8L,
    'failurecount':2L}
  spacemap_entry = post('http://192.168.59.103:4000/entries', data=spacemap_data).json()
  print spacemap_entry

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


  space_create = post('http://192.168.59.103:4000/space', data={'entry_space':'GeneralJournal'}).json()
  print space_create

def initialize_general_ledger():
  unique = uuid.uuid4()
  unique = str(unique)
  spacemap_data = {\
    'unique':unique,
    'entry_space':'spacemap',
    'nameofspace':'GeneralLedger',
    'keyname':'unique',
    'partitioncount':8L,
    'failurecount':2L}
  spacemap_entry = post('http://192.168.59.103:4000/entries', data=spacemap_data).json()
  print spacemap_entry


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

  space_create = post('http://192.168.59.103:4000/space', data={'entry_space':'GeneralLedger'}).json()
  print space_create


if __name__ == '__main__':
  reset_system()
  initialize_general_journal()
  initialize_general_ledger()
