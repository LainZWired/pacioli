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
from pacioli import app, db, models
from werkzeug import secure_filename


def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']



# Assumes a Werkzeug File Storage object: http://werkzeug.pocoo.org/docs/0.9/datastructures/#werkzeug.datastructures.FileStorage
def process(file):
  if allowed_file(file.filename):
    memoranda_id = str(uuid.uuid4())
    uploadDate = datetime.now()
    fileName = secure_filename(file.filename)
    fileType = fileName.rsplit('.', 1)[1]
    file.seek(0, os.SEEK_END)
    fileSize = file.tell()
    fileText = file.stream.getvalue().decode('UTF-8')
    document = io.StringIO(fileText)
    memo = models.Memoranda(id=memoranda_id, date=uploadDate, fileName=fileName, fileType=fileType, file=file.stream.getvalue(), fileSize=fileSize)
    db.session.add(memo)
    db.session.commit()
    if fileType == 'csv':
      reader = csv.reader(document)
      # Numbering each row
      reader = enumerate(reader)
      # Turns the enumerate object into a list
      rows = [pair for pair in reader]
      # Find the first longest list:
      header = max(rows, key=lambda tup:len(tup[1]))
      if header[1] == ['Confirmed', 'Date', 'Type', 'Label', 'Address', 'Amount', 'ID']:
        return _import_bitcoin_core(rows, header, memoranda_id)
      elif header[1] == ['Date', 'Description', 'Amount (BTC)', 'Amount ($)', 'Transaction Id']:
        return _import_multibit(rows, header, memoranda_id)
      elif header[1] == ['Date', 'Transaction ID', '#Conf', 'Wallet ID', 'Wallet Name', 'Credit', 'Debit', 'Fee (paid by this wallet)', 'Wallet Balance', 'Total Balance', 'Label']:
        return _import_armory(rows, header, memoranda_id)
      elif header[1] == ["transaction_hash","label", "confirmations", "value", "fee", "balance", "timestamp"]:
        return _import_electrum(rows, header, memoranda_id)
      else:
        return False
    return False

def _import_bitcoin_core(rows, header, memoranda_id):
  for row in rows:
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_transactions_id = str(uuid.uuid4())
      tx_details = str(memoranda)
      memoranda_transaction = models.MemorandaTransactions(id=memoranda_transactions_id, memoranda_id=memoranda_id, details=tx_details)
      db.session.add(memoranda_transaction)
      db.session.commit()

      journal_entry_id = str(uuid.uuid4())
      date = datetime.strptime(memoranda['Date'], "%Y-%m-%dT%H:%M:%S")
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(abs(float(memoranda['Amount']))*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(abs(float(memoranda['Amount']))*100000000) < 0:
        debit_ledger_account = "Expense"
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis",journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)
      
      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(abs(float(memoranda['Amount']))*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(abs(float(memoranda['Amount']))*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)

      db.session.commit()
  return True

def _import_multibit(rows, header, memoranda_id):
  logging.info(rows)
  for row in rows:
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_transactions_id = str(uuid.uuid4())
      tx_details = str(memoranda)
      memoranda_transaction = models.MemorandaTransactions(id=memoranda_transactions_id, memoranda_id=memoranda_id, details=tx_details)
      db.session.add(memoranda_transaction)
      db.session.commit()

      journal_entry_id = str(uuid.uuid4())
      date = datetime.strptime(memoranda['Date'], "%d %b %Y %H:%M")
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      if int(abs(float(memoranda['Amount (BTC)']))*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(abs(float(memoranda['Amount (BTC)']))*100000000) < 0:
        debit_ledger_account = "Expense"
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis",journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      if int(abs(float(memoranda['Amount (BTC)']))*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(abs(float(memoranda['Amount (BTC)']))*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)

      db.session.commit()
  return True

# header[1] == ['Date', 'Transaction ID', '#Conf', 'Wallet ID', 'Wallet Name', 'Credit', 'Debit', 'Fee (paid by this wallet)', 'Wallet Balance', 'Total Balance', 'Label']:

def _import_armory(rows, header, memoranda_id):
  for row in rows:
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_transactions_id = str(uuid.uuid4())
      tx_details = str(memoranda)
      memoranda_transaction = models.MemorandaTransactions(id=memoranda_transactions_id, memoranda_id=memoranda_id, details=tx_details)
      db.session.add(memoranda_transaction)
      db.session.commit()

      journal_entry_id = str(uuid.uuid4())
      date = datetime.strptime(memoranda['Date'], "%Y-%b-%d %I:%M%p")
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      if int(abs(float(memoranda['Credit']))*100000000) > 0:
        debit_ledger_amount = int(abs(float(memoranda['Credit']))*100000000)
        debit_ledger_account = "Bitcoins"
      elif int(abs(float(memoranda['Debit']))*100000000) < 0:
        debit_ledger_amount = int(abs(float(memoranda['Debit']))*100000000)
        debit_ledger_account = "Expense"
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis",journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      if int(abs(float(memoranda['Credit']))*100000000) > 0:
        credit_ledger_amount = int(abs(float(memoranda['Credit']))*100000000)
        credit_ledger_account = "Revenue"
      elif int(abs(float(memoranda['Debit']))*100000000) < 0:
        credit_ledger_amount = int(abs(float(memoranda['Debit']))*100000000)
        credit_ledger_account = "Bitcoins"
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)

      db.session.commit()
  return True

# elif header[1] == ["transaction_hash","label", "confirmations", "value", "fee", "balance", "timestamp"]:


def _import_electrum(rows, header, memoranda_id):
  for row in rows:
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      memoranda_transactions_id = str(uuid.uuid4())
      tx_details = str(memoranda)
      memoranda_transaction = models.MemorandaTransactions(id=memoranda_transactions_id, memoranda_id=memoranda_id, details=tx_details)
      db.session.add(memoranda_transaction)
      db.session.commit()

      journal_entry_id = str(uuid.uuid4())
      date = memoranda['timestamp']
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(abs(float(memoranda['value']))*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(abs(float(memoranda['value']))*100000000) < 0:
        debit_ledger_account = "Expense"
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis",journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(abs(float(memoranda['value']))*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(abs(float(memoranda['value']))*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)

      db.session.commit()

  return True
