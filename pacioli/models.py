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

from pacioli import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import BigInteger


# Memoranda are source documents from which accounting information is extracted to form General Journal entries. As a preliminary step, all of the details for each individual transaction are extracted from the source document to a dictionary.


class Memoranda(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime, index=True)
    fileName = db.Column(db.Text, unique=True)
    fileType = db.Column(db.Text)
    fileSize = db.Column(BigInteger)
    fileText = db.Column(db.Text)
    
    def __init__(self, id, date, fileName, fileType, fileSize, fileText):
        self.id = id
        self.date = date
        self.fileName = fileName
        self.fileType = fileType
        self.fileSize = fileSize
        self.fileText = fileText
        
    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.fileName)

class MemorandaTransactions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    details = db.Column(JSON)
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))
    
    def __init__(self, id, memoranda_id, details):
        self.id = id
        self.memoranda_id = memoranda_id
        self.details = details

    def __repr__(self):
        return '<id %r> <details %r>' % (self.id, self.details)

# There is a one to many relationship between Journal entries and Ledger entries. Every journal entry is composed of at least one debit and at least one credit. Total credits and total debits must always be equal.


class JournalEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))

    def __init__(self, id, memoranda_transactions_id):
        self.id = id
        self.memoranda_transactions_id = memoranda_transactions_id

        
    def __repr__(self):
        return '<id %r>' % (self.id)

class LedgerEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    entryType = db.Column(db.Text)
    account = db.Column(db.Text)
    amount = db.Column(BigInteger)
    unit = db.Column(db.Text)
    rate = db.Column(db.Float)
    fiat = db.Column(db.Float)
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))
    
    def __init__(self, id, date, entryType, account, amount, unit, rate, fiat, journal_entry_id):
        self.id = id
        self.date = date
        self.entryType = entryType
        self.account = account
        self.amount = amount
        self.unit = unit
        self.rate = rate
        self.fiat = fiat
        self.journal_entry_id = journal_entry_id
        
    def __repr__(self):
        return '<id %r>' % (self.id)

class PriceFeeds(db.Model):
    price_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger)
    price = db.Column(db.Float)
    volume = db.Column(db.Float)

class Prices(db.Model):
    date = db.Column(db.BigInteger, primary_key=True)
    source = db.Column(db.Text)
    currency = db.Column(db.Text)
    rate = db.Column(db.Integer)
    
    def __init__(self, date, source, currency, rate):
        self.date = date
        self.source = source
        self.currency = currency
        self.rate = rate
        
    def __repr__(self):
        return '<id %r>' % (self.id)
