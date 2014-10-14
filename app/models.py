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

from app import db
from sqlalchemy.dialects.postgresql import JSON


# Memoranda are source documents from which accounting information is extracted to form General Journal entries. As a preliminary step, all of the details for each individual transaction are extracted from the source document to a dictionary with a user-created File Mapping. After the raw transactions are extracted, they are transformed into ledger entries according to the rules set out in the Transaction Mappings.


class Memoranda(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime, index=True)
    fileName = db.Column(db.Text)
    fileType = db.Column(db.Text)
    fileSize = db.Column(db.Integer)
    file = db.Column(db.LargeBinary)
  #  fileMap_id = db.Column(db.Text, db.ForeignKey('file_maps.id'))
    
    def __init__(self, id, date, fileName, fileType, fileSize, file, fileMap_id):
        self.id = id
        self.date = date
        self.fileName = fileName
        self.fileType = fileType
        self.fileSize = fileSize
        self.file = file
        self.fileMap_id = fileMap_id
        
    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.fileName)

class MemorandaTransactions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    details = db.Column(JSON)
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))
    
    def __init__(self, id, memoranda_id, details, transactionMapName):
        self.id = id
        self.memoranda_id = memoranda_id
        self.details = details
        self.transactionMap_id = transactionMap_id

        
    def __repr__(self):
        return '<id %r> <details %r>' % (self.id, self.details)

# There is a one to many relationship between Journal entries and Ledger entries. Every journal entry is composed of at least one debit and at least one credit. Total credits and total debits must always be equal.


class JournalEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    memorandaTransactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))


    def __init__(self, id, date):
        self.id = id
        self.date = date

        
    def __repr__(self):
        return '<id %r>' % (self.id)

class LedgerEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    entryType = db.Column(db.Text)
    account = db.Column(db.Text)
    amount = db.Column(db.Integer)
    unit = db.Column(db.Text)
    journal_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))
    
    def __init__(self, id, date, entryType, account, amount, unit, journal_id):
        self.id = id
        self.date = date
        self.entryType = entryType
        self.account = account
        self.amount = amount
        self.unit = unit
        self.journal_id = journal_id
        
    def __repr__(self):
        return '<id %r>' % (self.id)
