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

class MemorandaTransactions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    txid = db.Column(db.Text)
    details = db.Column(JSON)
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))

class BitcoinTransactions(db.Model):
    # txid of the bitcoins received
    txid = db.Column(db.Text, primary_key=True)
    # output index of the bitcoins received
    output_index = db.Column(db.Integer, primary_key=True)
    # address the bitcoins were received with
    output_address = db.Column(db.Text)
    amount = db.Column(BigInteger)
    unspent = db.Column(db.Boolean)
    last_updated = db.Column(db.DateTime)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))

class Elements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    classifications = db.relationship('Classifications', backref='element', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class Classifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('elements.name'))
    accounts = db.relationship('Accounts', backref='classification', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name
        
class Accounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('classifications.name'))
    subacounts = db.relationship('Subaccounts', backref='account', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class Subaccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('accounts.name'))
    ledgerentries = db.relationship('LedgerEntries', backref='subaccount', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class JournalEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))
    ledgerentries = db.relationship('LedgerEntries', backref='journalentry', lazy='select', cascade="save-update, merge, delete")

class LedgerEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    tside = db.Column(db.Text)
    amount = db.Column(BigInteger)
    currency = db.Column(db.Text)
    ledger = db.Column(db.Text, db.ForeignKey('subaccounts.name'))
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))

class PriceFeeds(db.Model):
    price_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger)
    price = db.Column(db.Float)
    volume = db.Column(db.Float)

class Rates(db.Model):
    date = db.Column(db.BigInteger, primary_key=True)
    source = db.Column(db.Text)
    currency = db.Column(db.Text)
    rate = db.Column(db.Integer)
