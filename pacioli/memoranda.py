# Copyright (c) 2014, Satoshi Nakamoto Institute
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import fnmatch
import io
from datetime import datetime
import logging
import sys
import csv
import json
import uuid
from pacioli import app, db, models
import pacioli.prices as prices
from werkzeug import secure_filename
from dateutil import parser


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
      elif header[1] == ["Timestamp","Balance","BTC Amount","To","Notes","Instantly Exchanged","Transfer Total","Transfer Total Currency","Transfer Fee","Transfer Fee Currency","Transfer Payment Method","Transfer ID","Order Price","Order Currency","Order BTC","Order Tracking Code","Order Custom Parameter","Order Paid Out","Recurring Payment ID","Coinbase ID (visit https://www.coinbase.com/transactions/[ID] in your browser)","Bitcoin Hash (visit https://www.coinbase.com/tx/[HASH] in your browser for more info)"]:
        return _import_coinbase(rows, header, memoranda_id)
    elif header[1] == ["timestamp","price", "quantity"]:
        return _import_price_bitstamp(rows, header, memoranda_id)
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
      date = parser.parse(memoranda['Date'])
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(float(memoranda['Amount'])*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(float(memoranda['Amount'])*100000000) < 0:
        debit_ledger_account = "Expense"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis",rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)
      
      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(float(memoranda['Amount'])*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(float(memoranda['Amount'])*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
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
      date = parser.parse(memoranda['Date'])
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      if int(float(memoranda['Amount (BTC)'])*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(float(memoranda['Amount (BTC)'])*100000000) < 0:
        debit_ledger_account = "Expense"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount (BTC)']))*100000000)
      if int(float(memoranda['Amount (BTC)'])*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(float(memoranda['Amount (BTC)'])*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
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
      date = parser.parse(memoranda['Date'])
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      if int(float(memoranda['Credit'])*100000000) > 0:
        debit_ledger_amount = int(abs(float(memoranda['Credit']))*100000000)
        debit_ledger_account = "Bitcoins"
      elif int(float(memoranda['Debit'])*100000000) < 0:
        debit_ledger_amount = int(abs(float(memoranda['Debit']))*100000000)
        debit_ledger_account = "Expense"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      if int(float(memoranda['Credit'])*100000000) > 0:
        credit_ledger_amount = int(abs(float(memoranda['Credit']))*100000000)
        credit_ledger_account = "Revenue"
      elif int(float(memoranda['Debit'])*100000000) < 0:
        credit_ledger_amount = int(abs(float(memoranda['Debit']))*100000000)
        credit_ledger_account = "Bitcoins"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
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
      date = parser.parse(memoranda['timestamp'])
      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(float(memoranda['value'])*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(float(memoranda['value'])*100000000) < 0:
        debit_ledger_account = "Expense"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['Amount']))*100000000)
      if int(float(memoranda['value'])*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(float(memoranda['value'])*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)

      db.session.commit()

  return True
  
def _import_coinbase(rows, header, memoranda_id):
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
      date = parser.parse(memoranda['Timestamp'])

      journal_entry = models.JournalEntries(id=journal_entry_id, date=date, memoranda_transactions_id=memoranda_transactions_id)
      db.session.add(journal_entry)
      db.session.commit()

      debit_ledger_entry_id = str(uuid.uuid4())
      debit_ledger_amount = int(abs(float(memoranda['BTC Amount']))*100000000)
      if int(float(memoranda['BTC Amount'])*100000000) > 0:
        debit_ledger_account = "Bitcoins"
      elif int(float(memoranda['BTC Amount'])*100000000) < 0:
        debit_ledger_account = "Expense"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, entryType="debit", account=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(debit_ledger_entry)

      credit_ledger_entry_id = str(uuid.uuid4())
      credit_ledger_amount = int(abs(float(memoranda['BTC Amount']))*100000000)
      if int(float(memoranda['BTC Amount'])*100000000) > 0:
        credit_ledger_account = "Revenue"
      elif int(float(memoranda['BTC Amount'])*100000000) < 0:
        credit_ledger_account = "Bitcoins"
      rate = prices.getRate(date)
      fiat = debit_ledger_amount/100000000*rate
      credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, entryType="credit", account=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
      db.session.add(credit_ledger_entry)
      db.session.commit()
  return True
