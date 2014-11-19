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

import uuid
import datetime
from dateutil import parser
from collections import OrderedDict
from sqlalchemy.sql import func
from pacioli import db, models
import pacioli.accounting.rates as rates

class Partial:
    def __init__(self, date, debit, credit, currency, ledger, journal_entry_id, rate):
        self.date = date
        self.debit = debit
        self.credit = credit
        self.currency = currency
        self.ledger = ledger
        self.journal_entry_id = journal_entry_id
        self.rate = rate

def calculate_bitcoin_gains(method):
    usdtransactions = db.session \
        .query(models.LedgerEntries) \
        .filter(models.LedgerEntries.currency == 'USD') \
        .delete()

    transactions = db.session \
        .query(models.LedgerEntries) \
        .join(models.Subaccounts)\
        .join(models.Accounts)\
        .filter(models.Accounts.name == 'Bitcoins') \
        .filter(models.LedgerEntries.currency == 'Satoshis') \
        .order_by(models.LedgerEntries.date.desc())\
        .all()

    inventory = []
    
    while transactions:
        tx = transactions.pop()
        print('transaction')
        print(tx.date)
        print(tx.debit)
        print(tx.credit)
        tx_rate = rates.getRate(tx.date)
        if tx.debit > 0:
            inventory.insert(0, tx)
            tx.rate = tx_rate
            amount = tx.debit*tx_rate/100000000
            debit_ledger_entry_id = str(uuid.uuid4())
            debit_ledger_entry = models.LedgerEntries(
                id=debit_ledger_entry_id,
                date=tx.date, 
                ledger=tx.ledger, 
                debit=amount,
                credit=0,
                currency="USD", 
                journal_entry_id=tx.journal_entry_id)

            db.session.add(debit_ledger_entry)

            credit_ledger_entry_id = str(uuid.uuid4())
            credit_ledger_entry = models.LedgerEntries(
                id=credit_ledger_entry_id,
                date=tx.date, 
                debit=0, 
                credit=amount, 
                ledger="Revenues", 
                currency="USD", 
                journal_entry_id=tx.journal_entry_id)

            db.session.add(credit_ledger_entry)
            db.session.commit()
            
            if method == 'hifo':
                inventory.sort(key=lambda x: x.rate)

        elif tx.credit > 0:
            if method in ['fifo','hifo']:
                layer = inventory.pop()
            elif method == 'lifo':
                layer = inventory.pop(0)
                
            print('layer')
            print(layer.date)
            print(layer.credit)
            # layer_rate = rates.getRate(layer.date)
            layer_rate = layer.rate
            layer_costbasis = layer_rate*layer.credit/100000000
            if tx.credit > layer.debit:
                satoshis_sold = layer.debit
                salevalue = satoshis_sold * tx_rate/100000000
                costbasis = satoshis_sold * layer_rate/100000000
                gain = salevalue - costbasis
                residual_amount = tx.credit - satoshis_sold
                new_tx = Partial(
                    date=tx.date,
                    debit=0,
                    credit=residual_amount,
                    currency=tx.currency,
                    ledger=tx.ledger,
                    journal_entry_id=tx.journal_entry_id,
                    rate=tx_rate)
                print('new transaction')
                print(new_tx.date)
                print(new_tx.credit)
                transactions.append(new_tx)
                
            elif tx.credit < layer.debit:
                satoshis_sold = tx.credit
                salevalue = tx_rate * satoshis_sold/100000000
                costbasis = layer_rate * satoshis_sold/100000000
                gain = salevalue - costbasis
                residual_amount = layer.debit - satoshis_sold
                new_layer = Partial(
                    date = layer.date,
                    debit = residual_amount,
                    credit = 0,
                    currency = layer.currency,
                    ledger = layer.ledger,
                    journal_entry_id = layer.journal_entry_id,
                    rate = layer.rate)
                print('new layer')
                print(new_layer.date)
                print(new_layer.debit)
                inventory.append(new_layer)
            elif tx.credit == layer.debit:
                satoshis_sold = tx.credit
                salevalue = tx_rate * satoshis_sold/100000000
                costbasis = layer_rate * satoshis_sold/100000000
                gain = salevalue - costbasis
            
            if gain:
                if gain > 0:
                    debit = 0
                    credit = abs(gain)
                    gain_ledger = 'Gains from the Sale of Bitcoins'
                elif gain < 0:
                    debit = abs(gain)
                    credit = 0
                    gain_ledger = 'Losses from the Sale of Bitcoins'
                gain_leger_entry_id = str(uuid.uuid4())
                gain_ledger_entry = models.LedgerEntries(
                    id=gain_leger_entry_id,
                    date=tx.date, 
                    debit=debit,
                    credit=credit, 
                    ledger=gain_ledger, 
                    currency="USD", 
                    journal_entry_id=tx.journal_entry_id)
                    
                db.session.add(gain_ledger_entry)

            debit_ledger_entry_id = str(uuid.uuid4())
            debit_ledger_entry = models.LedgerEntries(
                id=debit_ledger_entry_id,
                date=tx.date, 
                debit=salevalue,
                credit=0, 
                ledger="Expenses", 
                currency="USD", 
                journal_entry_id=tx.journal_entry_id)
                
            db.session.add(debit_ledger_entry)
            
            credit_ledger_entry_id = str(uuid.uuid4())
            credit_ledger_entry = models.LedgerEntries(
                id=credit_ledger_entry_id,
                date=tx.date, 
                debit=0, 
                credit=costbasis, 
                ledger=tx.ledger, 
                currency="USD", 
                journal_entry_id=tx.journal_entry_id)
                
            db.session.add(credit_ledger_entry)

            db.session.commit()
