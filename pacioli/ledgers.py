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

import datetime
from collections import OrderedDict
from sqlalchemy.sql import func
from pacioli import db, models, rates
from dateutil import parser

def query_entries(accountName, groupby):
  if groupby == "All":
    ledger_entries = models.LedgerEntries.query.\
      filter_by(account=accountName).\
      order_by(models.LedgerEntries.date.desc()).\
      order_by(models.LedgerEntries.tside.desc()).all()
    account = foot_account(accountName, ledger_entries, 'All')
  elif groupby == "Daily":
    debit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(tside='debit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date)).all()
    credit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(tside='credit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date)).all()
    ledger_entries = {}
    for entry in debit_ledger_entries:
      day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
      if not day in ledger_entries:
        ledger_entries[day] = {}
      ledger_entries[day]['debit'] = int(entry[3])
    for entry in credit_ledger_entries:
      day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
      if not day in ledger_entries:
        ledger_entries[day] = {}
      ledger_entries[day]['credit'] = int(entry[3])
    ledger_entries = OrderedDict(sorted(ledger_entries.items()))
    account = foot_account(accountName, ledger_entries, 'Summary')
  elif groupby == "Monthly":
    debit_ledger_entries = db.session.query(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date),\
        func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(tside='debit').\
      group_by(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)).all()
    credit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(tside='credit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date)).all()
    ledger_entries = {}
    for entry in debit_ledger_entries:
      month = datetime.date(int(entry[0]), int(entry[1]), 1)
      if not month in ledger_entries:
        ledger_entries[month] = {}
      ledger_entries[month]['debit'] = int(entry[2])
    for entry in credit_ledger_entries:
      month = datetime.date(int(entry[0]), int(entry[1]), 1)
      if not month in ledger_entries:
        ledger_entries[month] = {}
      ledger_entries[month]['credit'] = int(entry[2])
    ledger_entries = OrderedDict(sorted(ledger_entries.items()))
    account = foot_account(accountName, ledger_entries, 'Summary')
  return [account, ledger_entries]

def foot_account(accountName, entries, interval):
  account = {}
  account['accountName'] = accountName
  account['totalDebit'] = 0
  account['totalCredit'] = 0
  account['debitBalance'] = 0
  account['creditBalance'] = 0
  if interval == 'All':
    for entry in entries:
      if entry.tside == 'debit' and entry.account == account['accountName']:
        account['totalDebit'] += entry.amount
      elif entry.tside == 'credit' and entry.account == account['accountName']:
        account['totalCredit'] += entry.amount
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
  elif interval == 'Summary':
    for entry in entries:
      if 'debit' in entries[entry]:
        account['totalDebit'] += entries[entry]['debit']
      if 'credit' in entries[entry]:
        account['totalCredit'] += entries[entry]['credit']
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
    
def get_balance(accountName, querydate):
    if type(querydate) is not datetime.datetime:
        querydate = parser.parse(querydate)
    transactions = query = db.session.query(\
      models.LedgerEntries.amount,\
      models.LedgerEntries.date,\
      models.LedgerEntries.tside).\
      filter(models.LedgerEntries.account_name==accountName, models.LedgerEntries.date <= querydate).\
      all()
    balance = 0
    for transaction in transactions:
        if transaction[2] == 'debit':
            balance += transaction[0]
        elif transaction[2] == 'credit':
            balance -= transaction[0]
    if balance > 0:
        debitBalance = balance
        creditBalance = 0
    elif balance < 0:
        debitBalance = 0
        creditBalance = balance
    else:
        debitBalance = 0
        creditBalance = 0
    balance = {'accountName': accountName,\
     'debitBalance' : debitBalance,\
     'creditBalance' : creditBalance}
    return balance

def get_fifo_costbasis(accountName, querydate):
    if type(querydate) is not datetime.datetime:
        querydate = parser.parse(querydate)
    transactions = db.session\
        .query(\
            models.LedgerEntries.amount,\
            models.LedgerEntries.rate,\
            models.LedgerEntries.fiat,\
            models.LedgerEntries.tside,\
            models.LedgerEntries.date)\
        .filter(models.LedgerEntries.account_name==accountName, models.LedgerEntries.date.__le__(querydate))\
        .order_by(models.LedgerEntries.date.desc())\
        .all()
    inventory = []
    costbasis = 0
    amount = 0
    transactions = [list(tx) for tx in transactions]
    while transactions:
        transaction = transactions.pop()
        if transaction[3] == 'debit':
            inventory.insert(0, transaction)
        elif transaction[3] == 'credit':
            tx_satoshis = transaction[0]
            tx_historical_rate = transaction[1]
            tx_costbasis = transaction[2]
            tx_type = transaction[3]
            tx_date = transaction[4]
            layer = inventory.pop()
            layer_satoshis = layer[0]
            layer_rate = layer[1]
            layer_costbasis = layer[2]
            if tx_type == 'debit':
                inventory.insert(0, transaction)
            elif tx_type == 'credit':
                if tx_satoshis > layer_satoshis:
                    saleprice = rates.getRate(tx_date)
                    satoshis_sold = layer_satoshis
                    salevalue = saleprice * satoshis_sold/100000000
                    costbasis = satoshis_sold * tx_historical_rate/100000000
                    residual_amount = tx_satoshis - satoshis_sold
                    residual_fiat = residual_amount*tx_historical_rate/100000000
                    new_transaction = [residual_amount, tx_historical_rate, residual_fiat, 'credit', tx_date]
                    transactions.append(new_transaction)
                elif tx_satoshis < layer_satoshis:
                    saleprice = rates.getRate(tx_date)
                    satoshis_sold = tx_satoshis
                    salevalue = saleprice * satoshis_sold/100000000
                    costbasis = satoshis_sold * layer_rate/100000000
                    residual_amount = layer_satoshis - satoshis_sold
                    residual_fiat = residual_amount*layer_rate/100000000
                    new_layer = [residual_amount, layer_rate, residual_fiat, 'debit']
                    inventory.append(new_layer)
                elif tx_satoshis == layer_satoshis:
                    saleprice = rates.getRate(tx_date)
                    satoshis_sold = tx_satoshis
                    salevalue = saleprice * satoshis_sold/100000000
                    costbasis = tx_costbasis
    if inventory:
        for layer in inventory:
            amount += layer[0]
            costbasis += layer[2]
        rate = round(costbasis/amount*100000000, 2)
        return [amount, rate, costbasis, 'debit']
    else:
        return [0, 0, 0, 0]
    
    
def get_fifo_unrealized_gain(accountName, querydate):
    if type(querydate) is not datetime.datetime:
        querydate = parser.parse(querydate)
    costbasis = get_fifo_costbasis(accountName, querydate)
    balance = get_balance(accountName, querydate)
    querydate = parser.parse(querydate)
    valuation = rates.getRate(querydate)
    valuation = valuation * balance/100000000
    gain = valuation - costbasis[2]
    return gain

def get_fifo_realized_gain(accountName, startDate, endDate):
    if type(startDate) is not datetime.datetime:
        startDate = parser.parse(startDate)
    if type(endDate) is not datetime.datetime:
        endDate = parser.parse(endDate)
    transactions = db.session\
        .query(\
            models.LedgerEntries.amount,\
            models.LedgerEntries.rate,\
            models.LedgerEntries.fiat,\
            models.LedgerEntries.tside,\
            models.LedgerEntries.date)\
        .filter(models.LedgerEntries.account_name==accountName,\
            models.LedgerEntries.date\
                .between(startDate, endDate))\
        .order_by(models.LedgerEntries.date.desc())\
        .all()
    inventory = []
    gain = 0
    print(startDate)
    begbal = get_fifo_costbasis(accountName, startDate)
    inventory.insert(0, begbal)
    print(transactions)
    transactions = [list(tx) for tx in transactions]
    print(transactions)
    while transactions:
        transaction = transactions.pop()
        print('transaction')
        print(transaction)
        tx_satoshis = transaction[0]
        tx_historical_rate = transaction[1]
        tx_costbasis = transaction[2]
        tx_type = transaction[3]
        tx_date = transaction[4]
        layer = inventory.pop()
        print('layer')
        print(layer)
        layer_satoshis = layer[0]
        layer_rate = layer[1]
        layer_costbasis = layer[2]
        if tx_type == 'debit':
            inventory.insert(0, transaction)
        elif tx_type == 'credit':
            if tx_satoshis > layer_satoshis:
                saleprice = rates.getRate(tx_date)
                satoshis_sold = layer_satoshis
                salevalue = saleprice * satoshis_sold/100000000
                costbasis = satoshis_sold * tx_historical_rate/100000000
                gain += salevalue - costbasis
                residual_amount = tx_satoshis - satoshis_sold
                residual_fiat = residual_amount*tx_historical_rate/100000000
                new_transaction = [residual_amount, tx_historical_rate, residual_fiat, 'credit', tx_date]
                print('new transaction')
                print(new_transaction)
                transactions.append(new_transaction)
            elif tx_satoshis < layer_satoshis:
                saleprice = rates.getRate(tx_date)
                satoshis_sold = tx_satoshis
                salevalue = saleprice * satoshis_sold/100000000
                costbasis = satoshis_sold * layer_rate/100000000
                gain += salevalue - costbasis
                residual_amount = layer_satoshis - satoshis_sold
                residual_fiat = residual_amount*layer_rate/100000000
                new_layer = [residual_amount, layer_rate, residual_fiat, 'debit']
                print('new layer')
                print(new_layer)
                inventory.append(new_layer)
            elif tx_satoshis == layer_satoshis:
                saleprice = rates.getRate(tx_date)
                satoshis_sold = tx_satoshis
                salevalue = saleprice * satoshis_sold/100000000
                costbasis = tx_costbasis
                gain += salevalue - costbasis
    return gain
