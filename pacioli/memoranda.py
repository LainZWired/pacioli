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
from pacioli import app, db, models, blockchain
import pacioli.rates as rates
from werkzeug import secure_filename
from dateutil import parser


def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Assumes a Werkzeug File Storage object: http://werkzeug.pocoo.org/docs/0.9/datastructures/#werkzeug.datastructures.FileStorage
def process_filestorage(file):
  if allowed_file(file.filename):
    fileName = secure_filename(file.filename)
    fileType = fileName.rsplit('.', 1)[1]
    file.seek(0, os.SEEK_END)
    fileSize = file.tell()
    fileText = file.stream.getvalue().decode('UTF-8')
    process_memoranda(fileName, fileType, fileSize, fileText)
    
def process_memoranda(fileName, fileType, fileSize, fileText):
    uploadDate = datetime.now()
    memoranda_id = str(uuid.uuid4())
    memo = models.Memoranda(id=memoranda_id, date=uploadDate, fileName=fileName, fileType=fileType, fileText=fileText, fileSize=fileSize)
    db.session.add(memo)
    db.session.commit()
    document = io.StringIO(fileText)
    if fileType == 'csv':
        process_csv(document, memoranda_id)
        
def process_csv(document, memoranda_id):
    reader = csv.reader(document)
    reader = enumerate(reader)
    rows = [pair for pair in reader]
    header = max(rows, key=lambda tup:len(tup[1]))
    for row in rows:
      if row[0] > header[0] and len(row[1]) == len(header[1]):
        memoranda = zip(header[1], row[1])
        memoranda = dict(memoranda)

        # Bitcoin Core
        if header[1] == ['Confirmed', 'Date', 'Type', 'Label', 'Address', 'Amount', 'ID']:
            address = memoranda['Address']
            txid = memoranda['ID'][:64]
            date = parser.parse(memoranda['Date'])
            amount = int(float(memoranda['Amount'])*100000000)
            debit_ledger_amount = abs(amount)
            credit_ledger_amount = abs(amount)
            if amount > 0:
                debit_ledger_account = "Bitcoins"
                credit_ledger_account = "Revenues"
            elif amount < 0:
                debit_ledger_account = "Expenses"
                credit_ledger_account = "Bitcoins"
              
        # MultiBit
        elif header[1] == ['Date', 'Description', 'Amount (BTC)', 'Amount ($)', 'Transaction Id']:
            address = memoranda['Description']
            address = address.split('(')[-1]
            address = address.replace(r"\(.*\)","")
            txid = memoranda['Transaction Id']
            date = parser.parse(memoranda['Date'])
            amount = int(float(memoranda['Amount (BTC)'])*100000000)
            debit_ledger_amount = abs(amount)
            credit_ledger_amount = abs(amount)
            if amount > 0:
                debit_ledger_account = "Bitcoins"
                credit_ledger_account = "Revenues"
            elif amount < 0:
                debit_ledger_account = "Expenses"
                credit_ledger_account = "Bitcoins"
        
        # Armory
        elif header[1] == ['Date', 'Transaction ID', '#Conf', 'Wallet ID', 'Wallet Name', 'Credit', 'Debit', 'Fee (paid by this wallet)', 'Wallet Balance', 'Total Balance', 'Label']:
            # Armory does not export the address you're receiving with  / sending to .... complain here: https://github.com/etotheipi/BitcoinArmory/issues/247
            address = ''
            txid = memoranda['Transaction ID']
            date = parser.parse(memoranda['Date'])
            fee = memoranda['Fee (paid by this wallet)']
            if fee == '':
                fee = 0
            else:
                fee = int(float(fee)*100000000)
            if memoranda['Credit'] == '':
                memoranda['Credit'] = 0
            if memoranda['Debit'] == '':
                memoranda['Debit'] = 0
            credit = int(float(memoranda['Credit'])*100000000)
            debit = int(float(memoranda['Debit'])*100000000)
            if credit > 0:
                debit_ledger_amount = abs(credit)
                debit_ledger_account = "Bitcoins"
                credit_ledger_amount = abs(credit)
                credit_ledger_account = "Revenues"
            elif debit > 0:
                debit_ledger_amount = abs(debit) - abs(fee)
                debit_ledger_account = "Expenses"
                credit_ledger_amount = abs(debit) - abs(fee)
                credit_ledger_account = "Bitcoins"

        # Electrum
        elif header[1] == ["transaction_hash","label", "confirmations", "value", "fee", "balance", "timestamp"]:
            address = ''
            # Electrum does not export the address you're receiving with  / sending to .... complain here: https://github.com/spesmilo/electrum/issues/911

            txid = memoranda['transaction_hash']
            date = parser.parse(memoranda['timestamp'])
            value = int(float(memoranda['value'])*100000000)
            fee = int(float(memoranda['fee'])*100000000)
            if value > 0:
                debit_ledger_amount = abs(value)
                debit_ledger_account = "Bitcoins"
                credit_ledger_amount = abs(value)
                credit_ledger_account = "Revenues"
            elif value < 0:
                debit_ledger_amount = abs(value) - abs(fee)
                debit_ledger_account = "Expenses"
                debit_ledger_amount = abs(value) - abs(fee)
                credit_ledger_account = "Bitcoins"

        #Coinbase
        elif header[1] == ["Timestamp","Balance","BTC Amount","To","Notes","Instantly Exchanged","Transfer Total","Transfer Total Currency","Transfer Fee","Transfer Fee Currency","Transfer Payment Method","Transfer ID","Order Price","Order Currency","Order BTC","Order Tracking Code","Order Custom Parameter","Order Paid Out","Recurring Payment ID","Coinbase ID (visit https://www.coinbase.com/transactions/[ID] in your browser)","Bitcoin Hash (visit https://www.coinbase.com/tx/[HASH] in your browser for more info)"]:
            address = memoranda['To']
            txid = memoranda['Bitcoin Hash (visit https://www.coinbase.com/tx/[HASH] in your browser for more info)'][:64]
            date = parser.parse(memoranda['Timestamp'])
            amount = int(float(memoranda['BTC Amount'])*100000000)
            debit_ledger_amount = abs(amount)
            credit_ledger_amount = abs(amount)
            if amount > 0:
                debit_ledger_account = "Bitcoins"
                credit_ledger_account = "Revenues"
            elif amount < 0:
                debit_ledger_account = "Expenses"
                credit_ledger_account = "Bitcoins"
        else:
            return False
            
        
        memoranda_transactions_id = str(uuid.uuid4())
        journal_entry_id = str(uuid.uuid4())
        debit_ledger_entry_id = str(uuid.uuid4())
        credit_ledger_entry_id = str(uuid.uuid4())
        
        # blockchain.get_transaction(txid)
        tx_details = str(memoranda)
        memoranda_transaction = models.MemorandaTransactions(id=memoranda_transactions_id, memoranda_id=memoranda_id, txid=txid, details=tx_details)
        db.session.add(memoranda_transaction)
        db.session.commit()
        journal_entry = models.JournalEntries(id=journal_entry_id, memoranda_transactions_id=memoranda_transactions_id)
        db.session.add(journal_entry)
        db.session.commit()
        
        rate = rates.getRate(date)
        fiat = debit_ledger_amount/100000000*rate
        debit_ledger_entry = models.LedgerEntries(id=debit_ledger_entry_id,date=date, tside="debit", account_name=debit_ledger_account, amount=debit_ledger_amount,unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
        db.session.add(debit_ledger_entry)
        credit_ledger_entry = models.LedgerEntries(id=credit_ledger_entry_id,date=date, tside="credit", account_name=credit_ledger_account, amount=credit_ledger_amount, unit="satoshis", rate=rate, fiat=fiat, journal_entry_id=journal_entry_id)
        db.session.add(credit_ledger_entry)
        db.session.commit()
