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
    def __init__(self, date, tside, amount, currency, ledger, journal_entry_id):
        self.date = date
        self.tside = tside
        self.amount = amount
        self.currency = currency
        self.ledger = ledger
        self.journal_entry_id = journal_entry_id

def calculate_bitcoin_gains(method):
    usdtransactions = db.session \
        .query(models.LedgerEntries) \
        .filter(models.LedgerEntries.currency == 'usd') \
        .delete()
    if method == "fifo":
        transactions = db.session \
            .query(models.LedgerEntries) \
            .join(models.Subaccounts)\
            .join(models.Accounts)\
            .filter(models.Accounts.name == 'Bitcoins') \
            .filter(models.LedgerEntries.currency == 'satoshis') \
            .order_by(models.LedgerEntries.date.desc())\
            .all()
        # split out transactions into debit and credit for FIFO/LIFO/HiFO
    inventory = []
    
    while transactions:
        tx = transactions.pop()
        print('transaction')
        print(tx.date)
        print(tx.amount)
        print(tx.tside)
        tx_rate = rates.getRate(tx.date)
        if tx.tside == 'debit':
            inventory.insert(0, tx)
            amount = tx.amount*tx_rate/100000000
            debit_ledger_entry_id = str(uuid.uuid4())
            debit_ledger_entry = models.LedgerEntries(
                id=debit_ledger_entry_id,
                date=tx.date, 
                tside="debit", 
                ledger=tx.ledger, 
                amount=amount,
                currency="usd", 
                journal_entry_id=tx.journal_entry_id)

            db.session.add(debit_ledger_entry)

            credit_ledger_entry_id = str(uuid.uuid4())
            credit_ledger_entry = models.LedgerEntries(
                id=credit_ledger_entry_id,
                date=tx.date, 
                tside="credit", 
                ledger="Revenues", 
                amount=amount, 
                currency="usd", 
                journal_entry_id=tx.journal_entry_id)

            db.session.add(credit_ledger_entry)
            db.session.commit()

        elif tx.tside == 'credit':
            layer = inventory.pop()
            print('layer')
            print(layer.date)
            print(layer.amount)
            layer_rate = rates.getRate(layer.date)
            layer_costbasis = layer_rate*layer.amount/100000000
            if tx.amount > layer.amount:
                satoshis_sold = layer.amount
                salevalue = satoshis_sold * tx_rate/100000000
                costbasis = satoshis_sold * layer_rate/100000000
                gain = salevalue - costbasis
                residual_amount = tx.amount - satoshis_sold
                new_tx = Partial(
                    date=tx.date,
                    tside=tx.tside,
                    amount=residual_amount,
                    currency=tx.currency,
                    ledger=tx.ledger,
                    journal_entry_id=tx.journal_entry_id)
                print('new transaction')
                print(new_tx.date)
                print(new_tx.amount)
                transactions.append(new_tx)
                
            elif tx.amount < layer.amount:
                satoshis_sold = tx.amount
                salevalue = tx_rate * satoshis_sold/100000000
                costbasis = layer_rate * satoshis_sold/100000000
                gain = salevalue - costbasis
                residual_amount = layer.amount - satoshis_sold
                new_layer = Partial(
                    date = layer.date,
                    tside = layer.tside,
                    amount = residual_amount,
                    currency = layer.currency,
                    ledger = layer.ledger,
                    journal_entry_id = layer.journal_entry_id)
                print('new layer')
                print(new_layer.date)
                print(new_layer.amount)
                inventory.append(new_layer)
            elif tx.amount == layer.amount:
                satoshis_sold = tx.amount
                salevalue = tx_rate * satoshis_sold/100000000
                costbasis = layer_rate * satoshis_sold/100000000
                gain = salevalue - costbasis
            
            if gain:
                if gain > 0:
                    gain_tside = 'credit'
                    gain_ledger = 'Gains from the Sale of Bitcoins'
                elif gain < 0:
                    gain_tside = 'debit'
                    gain_ledger = 'Losses from the Sale of Bitcoins'
                gain = abs(gain)
                gain_leger_entry_id = str(uuid.uuid4())
                gain_ledger_entry = models.LedgerEntries(
                    id=gain_leger_entry_id,
                    date=tx.date, 
                    tside=gain_tside, 
                    ledger=gain_ledger, 
                    amount=gain, 
                    currency="usd", 
                    journal_entry_id=tx.journal_entry_id)
                    
                db.session.add(gain_ledger_entry)

            debit_ledger_entry_id = str(uuid.uuid4())
            debit_ledger_entry = models.LedgerEntries(
                id=debit_ledger_entry_id,
                date=tx.date, 
                tside="debit", 
                ledger="Expenses", 
                amount=salevalue,
                currency="usd", 
                journal_entry_id=tx.journal_entry_id)
                
            db.session.add(debit_ledger_entry)
            
            credit_ledger_entry_id = str(uuid.uuid4())
            credit_ledger_entry = models.LedgerEntries(
                id=credit_ledger_entry_id,
                date=tx.date, 
                tside="credit", 
                ledger=tx.ledger, 
                amount=costbasis, 
                currency="usd", 
                journal_entry_id=tx.journal_entry_id)
                
            db.session.add(credit_ledger_entry)

            db.session.commit()
