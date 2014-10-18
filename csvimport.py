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

import os
import fnmatch
import io
from datetime import datetime, date, time, timezone
import logging
import sys
import csv
import json
import uuid
import api


logging.basicConfig(filename='CSV_Import_Module_Log.csv', \
  format='%(asctime)s %(message)s',\
  datefmt='%m/%d/%Y %I:%M:%S %p', \
  level=logging.INFO)

def csv_import(csvfile):
  with open(csvfile, 'rt') as csvfile:
    csvfile.seek(0, os.SEEK_END)
    csvbinary = io.StringIO(csvfile.read())
    csvbinary = csvbinary.getvalue()

    # Adding the metadata and the binary file to Memoranda
    memorandum = {}
    memorandum['entry_space'] = 'Memoranda'
    memorandum['unique'] = str(uuid.uuid4())
    now     = datetime.now()
    memorandum['Date'] = now.strftime("%s")
    memorandum['Filename'] = csvfile.name
    memorandum['Filetype'] = 'csv'
    memorandum['Filesize'] = csvfile.tell()
    memorandum['File'] = csvbinary
    logging.info(api.add_record(memorandum))

    # Adding individual CSV lines to the GeneralJournal and GeneralLedger
    csvfile.seek(0)
    reader = csv.reader(csvfile)
    # Numbering each row
    reader = enumerate(reader)
    # Turns the enumerate object into a list
    rows = [pair for pair in reader]
    # Find the first longest list:
    header = max(rows, key=lambda tup:len(tup[1]))
    logging.info(header)
    if header[1] == ['Confirmed', 'Date', 'Type', 'Label', 'Address', 'Amount', 'ID']:
      return _import_bitcoin_core(rows, header, memorandum['unique'])
    elif header[1] == ['Date', 'Description', 'Amount (BTC)', 'Amount ($)', 'Transaction Id']:
      return _import_multibit(rows, header, memorandum['unique'])
    elif header[1] == ['Date', 'Transaction ID', '#Conf', 'Wallet ID', 'Wallet Name', 'Credit', 'Debit', 'Fee (paid by this wallet)', 'Wallet Balance', 'Total Balance', 'Label']:
      return _import_armory(rows, header, memorandum['unique'])
    elif header[1] == ["transaction_hash","label", "confirmations", "value", "fee", "balance", "timestamp"]:
      return _import_electrum(rows, header, memorandum['unique'])
    else:
      logging.error(str(csvfile.name) + " Unrecognized file format: " + str(header))
      return False
  logging.error("Could not open file.")
  return False

def _import_bitcoin_core(rows, header, unique):
  logging.info(unique)
  for row in rows:
    logging.info(row)
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_entry = {}
      memoranda_entry['entry_space'] = 'MemorandaTransactions'
      memoranda_entry['unique'] = str(uuid.uuid4())
      memoranda_entry['MemorandaUnique'] = unique
      memoranda_entry['Details'] = str(memoranda)
      memoranda_entry['TransactionMapName'] = 'BitcoinCoreCSV'
      logging.info(api.add_record(memoranda_entry))

      journal_entry = {}
      journal_entry['entry_space'] = 'GeneralJournal'
      journal_entry['unique'] = str(uuid.uuid4())
      reformat = datetime.strptime(memoranda['Date'], "%Y-%m-%dT%H:%M:%S")
      reformat = reformat.strftime("%s")
      journal_entry['Date'] = reformat
      journal_entry['Debits'] = []
      journal_entry['Credits'] = []

      debit_ledger_entry = {}
      debit_ledger_entry['entry_space'] = 'GeneralLedger'
      debit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Debits'].append(debit_ledger_entry['unique'])
      debit_ledger_entry['Date'] = reformat
      debit_ledger_entry['Type'] = "Debit"
      debit_ledger_entry['Amount'] = int(abs(float(memoranda['Amount']))*100000000)
      debit_ledger_entry['Unit'] = "satoshis"
      debit_ledger_entry['gjUnique'] = journal_entry['unique']
      credit_ledger_entry = {}
      credit_ledger_entry['entry_space'] = 'GeneralLedger'
      credit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Credits'].append(debit_ledger_entry['unique'])
      journal_entry['Credits']
      credit_ledger_entry['Date'] = reformat
      credit_ledger_entry['Type'] = "Credit"
      credit_ledger_entry['Amount'] = int(abs(float(memoranda['Amount']))*100000000)
      credit_ledger_entry['Unit'] = "satoshis"
      credit_ledger_entry['gjUnique'] = journal_entry['unique']

      if int(abs(float(memoranda['Amount']))*100000000) > 0:
        debit_ledger_entry['Account'] = "Bitcoins"
        credit_ledger_entry['Account'] = "Revenue"
      elif int(abs(float(memoranda['Amount']))*100000000) < 0:
        debit_ledger_entry['Account'] = "Expense"
        credit_ledger_entry['Account'] = "Bitcoins"
      journal_entry['Debits']= set(journal_entry['Debits'])
      journal_entry['Credits']= set(journal_entry['Credits'])
      logging.info(api.add_record(journal_entry))
      logging.info(api.add_record(debit_ledger_entry))
      logging.info(api.add_record(credit_ledger_entry))
  return True

def _import_multibit(rows, header, unique):
  logging.info(rows)
  for row in rows:
    logging.info(row)
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_entry = {}
      memoranda_entry['entry_space'] = 'MemorandaTransactions'
      memoranda_entry['unique'] = str(uuid.uuid4())
      memoranda_entry['MemorandaUnique'] = unique
      memoranda_entry['Details'] = str(memoranda)
      memoranda_entry['TransactionMapName'] = 'MultiBitCSV'
      logging.info(api.add_record(memoranda_entry))

      journal_entry = {}
      journal_entry['entry_space'] = 'GeneralJournal'
      journal_entry['unique'] = str(uuid.uuid4())
      reformat = datetime.strptime(memoranda['Date'], "%d %b %Y %H:%M")
      reformat = reformat.strftime("%s")
      journal_entry['Date'] = reformat
      journal_entry['Debits'] = []
      journal_entry['Credits'] = []

      debit_ledger_entry = {}
      debit_ledger_entry['entry_space'] = 'GeneralLedger'
      debit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Debits'].append(debit_ledger_entry['unique'])
      debit_ledger_entry['Date'] = reformat
      debit_ledger_entry['Type'] = "Debit"
      debit_ledger_entry['Amount'] = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      debit_ledger_entry['Unit'] = "satoshis"
      debit_ledger_entry['gjUnique'] = journal_entry['unique']

      credit_ledger_entry = {}
      credit_ledger_entry['entry_space'] = 'GeneralLedger'
      credit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Credits'].append(debit_ledger_entry['unique'])
      journal_entry['Credits']
      credit_ledger_entry['Date'] = reformat
      credit_ledger_entry['Type'] = "Credit"
      credit_ledger_entry['Amount'] = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      credit_ledger_entry['Unit'] = "satoshis"
      credit_ledger_entry['gjUnique'] = journal_entry['unique']

      if int(abs(float(memoranda['Amount (BTC)']))*100000000) > 0:
        debit_ledger_entry['Account'] = "Bitcoins"
        credit_ledger_entry['Account'] = "Revenue"
      elif int(abs(float(memoranda['Amount (BTC)']))*100000000) < 0:
        debit_ledger_entry['Account'] = "Expense"
        credit_ledger_entry['Account'] = "Bitcoins"
      journal_entry['Debits']= set(journal_entry['Debits'])
      journal_entry['Credits']= set(journal_entry['Credits'])
      logging.info(api.add_record(journal_entry))
      logging.info(api.add_record(debit_ledger_entry))
      logging.info(api.add_record(credit_ledger_entry))
  return True

# header[1] == ['Date', 'Transaction ID', '#Conf', 'Wallet ID', 'Wallet Name', 'Credit', 'Debit', 'Fee (paid by this wallet)', 'Wallet Balance', 'Total Balance', 'Label']:

def _import_armory(rows, header, unique):
  logging.info(rows)
  for row in rows:
    logging.info(row)
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_entry = {}
      memoranda_entry['entry_space'] = 'MemorandaTransactions'
      memoranda_entry['unique'] = str(uuid.uuid4())
      memoranda_entry['MemorandaUnique'] = unique
      memoranda_entry['Details'] = str(memoranda)
      memoranda_entry['TransactionMapName'] = 'ArmoryCSV'
      logging.info(api.add_record(memoranda_entry))

      journal_entry = {}
      journal_entry['entry_space'] = 'GeneralJournal'
      journal_entry['unique'] = str(uuid.uuid4())
      journal_entry['Date'] = memoranda['Date']
      reformat = datetime.strptime(memoranda['Date'], "%Y-%b-%d %I:%M%p")
      reformat = reformat.strftime("%s")
      journal_entry['Date'] = reformat
      journal_entry['Debits'] = []
      journal_entry['Credits'] = []

      debit_ledger_entry = {}
      debit_ledger_entry['entry_space'] = 'GeneralLedger'
      debit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Debits'].append(debit_ledger_entry['unique'])
      debit_ledger_entry['Date'] = memoranda['Date']
      debit_ledger_entry['Type'] = "Debit"
      debit_ledger_entry['Unit'] = "satoshis"
      debit_ledger_entry['gjUnique'] = journal_entry['unique']

      credit_ledger_entry = {}
      credit_ledger_entry['entry_space'] = 'GeneralLedger'
      credit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Credits'].append(debit_ledger_entry['unique'])
      journal_entry['Credits']
      credit_ledger_entry['Date'] = memoranda['Date']
      credit_ledger_entry['Type'] = "Credit"
      credit_ledger_entry['Unit'] = "satoshis"
      credit_ledger_entry['gjUnique'] = journal_entry['unique']

      if int(abs(float(memoranda['Credit']))*100000000) > 0:
        debit_ledger_entry['Amount'] = int(abs(float(memoranda['Credit']))*100000000)
        credit_ledger_entry['Amount'] = int(abs(float(memoranda['Credit']))*100000000)
        debit_ledger_entry['Account'] = "Bitcoins"
        credit_ledger_entry['Account'] = "Revenue"
      elif int(abs(float(memoranda['Debit']))*100000000) < 0:
        debit_ledger_entry['Amount'] = int(abs(float(memoranda['Debit']))*100000000)
        credit_ledger_entry['Amount'] = int(abs(float(memoranda['Debit']))*100000000)
        debit_ledger_entry['Account'] = "Expense"
        credit_ledger_entry['Account'] = "Bitcoins"

      journal_entry['Debits']= set(journal_entry['Debits'])
      journal_entry['Credits']= set(journal_entry['Credits'])
      logging.info(api.add_record(journal_entry))
      logging.info(api.add_record(debit_ledger_entry))
      logging.info(api.add_record(credit_ledger_entry))
  return True

# elif header[1] == ["transaction_hash","label", "confirmations", "value", "fee", "balance", "timestamp"]:


def _import_electrum(rows, header, unique):
  logging.info(rows)
  for row in rows:
    logging.info(row)
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_entry = {}
      memoranda_entry['entry_space'] = 'MemorandaTransactions'
      memoranda_entry['unique'] = str(uuid.uuid4())
      memoranda_entry['MemorandaUnique'] = unique
      memoranda_entry['Details'] = str(memoranda)
      memoranda_entry['TransactionMapName'] = 'ArmoryCSV'
      logging.info(api.add_record(memoranda_entry))

      journal_entry = {}
      journal_entry['entry_space'] = 'GeneralJournal'
      journal_entry['unique'] = str(uuid.uuid4())
      journal_entry['Date'] = memoranda['timestamp']
      journal_entry['Debits'] = []
      journal_entry['Credits'] = []

      debit_ledger_entry = {}
      debit_ledger_entry['entry_space'] = 'GeneralLedger'
      debit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Debits'].append(debit_ledger_entry['unique'])
      debit_ledger_entry['Date'] = memoranda['timestamp']
      debit_ledger_entry['Type'] = "Debit"
      debit_ledger_entry['Amount'] = int(abs(float(memoranda['value']))*100000000)
      debit_ledger_entry['Unit'] = "satoshis"
      debit_ledger_entry['gjUnique'] = journal_entry['unique']

      credit_ledger_entry = {}
      credit_ledger_entry['entry_space'] = 'GeneralLedger'
      credit_ledger_entry['unique'] = str(uuid.uuid4())
      journal_entry['Credits'].append(debit_ledger_entry['unique'])
      journal_entry['Credits']
      credit_ledger_entry['Date'] = memoranda['timestamp']
      credit_ledger_entry['Type'] = "Credit"
      credit_ledger_entry['Amount'] = int(abs(float(memoranda['value']))*100000000)
      credit_ledger_entry['Unit'] = "satoshis"
      credit_ledger_entry['gjUnique'] = journal_entry['unique']

      if int(abs(float(memoranda['value']))*100000000) > 0:
        debit_ledger_entry['Account'] = "Bitcoins"
        credit_ledger_entry['Account'] = "Revenue"
      elif int(abs(float(memoranda['value']))*100000000) < 0:
        debit_ledger_entry['Account'] = "Expense"
        credit_ledger_entry['Account'] = "Bitcoins"
      journal_entry['Debits']= set(journal_entry['Debits'])
      journal_entry['Credits']= set(journal_entry['Credits'])
      logging.info(api.add_record(journal_entry))
      logging.info(api.add_record(debit_ledger_entry))
      logging.info(api.add_record(credit_ledger_entry))
  return True

def main():
    if len(sys.argv) <2:
        sys.exit('Missing argument: specify the folder of CSV files you want to convert.')
    logging.info(api.start_system())
    searchdir = sys.argv[1]
    matches = []
    for root, dirnames, filenames in os.walk('%s' % searchdir):
        for filename in fnmatch.filter(filenames, '*.csv'):
            matches.append(os.path.join(root,filename))
    logging.info(matches)
    for csvfile in matches:
        result = csv_import(csvfile)
        if not result:
            sys.exit(1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
