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
    details = db.Column(db.PickleType)
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))
    
    def __init__(self, id, memoranda_id, details, transactionMapName):
        self.id = id
        self.memoranda_id = memoranda_id
        self.details = details
        self.transactionMap_id = transactionMap_id

        
    def __repr__(self):
        return '<id %r> <details %r>' % (self.id, self.details)
    
# Transaction details are then converted into Journal entries with a user-created mapping.

# File maps are sets of mappings that correspond to a particular data source (for example a CSV export from MultiBit).

class FileMaps(db.Model):
    id = db.Column(db.Text, primary_key=True)
    fileMapName = db.Column(db.Text, unique=True)
    
    def __init__(self, id, fileMapName, memoranda):
        self.id = id
        self.fileMapName = fileMapName
        self.memoranda = memoranda
        self.fileMappings = fileMappings
        
    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.fileMapName)

# File Mappings explain how raw transaction information is extracted from the data source. This is trivial for a CSV with headers but can become complex for HTML, PDFs, e-mails, etc. The Transaction Key indicates what key:value pair will be populated in the memoranda transaction detail by the mapping. 


class FileMappings(db.Model):
    id = db.Column(db.Text, primary_key=True)
    fileMap_id = db.Column(db.Text, db.ForeignKey('file_maps.id'))
    fileMappingName = db.Column(db.Text, unique=True)
    fileMapping = db.Column(db.PickleType)
    transactionKey = db.Column(db.Text)
    
    def __init__(self, id, fileMap_id, fileMappingName, fileMapping, transactionKey):
        self.id = id
        self.fileMap_id = fileMap_id
        self.MappingName = MappingName
        self.fileMapping = fileMapping
        self.transactionKey = transactionKey
        
    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.MappingName)


# Transaction Mappings explain how Ledger entries are extracted from raw transaction information. Journal entries are automatically created based on the corresponding debit and credit ledger entries.


class TransactionMaps(db.Model):
    id = db.Column(db.Text, primary_key=True)
    transactionMapName = db.Column(db.Text)
    
    def __init__(self, id, transactionMapName):
        self.id = id
        self.transactionMapName = transactionMapName

    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.transactionMapName)


class TransactionMappings(db.Model):
    id = db.Column(db.Text, primary_key=True)
    transactionMappingName = db.Column(db.Text)
    transactionMapping = db.Column(db.PickleType)
    ledgerKey = db.Column(db.Text)
    transactionMap_id = db.Column(db.Text, db.ForeignKey('transaction_maps.id'))
    
    def __init__(self, id, transactionMappingName, transactionMapping, ledgerKey, transactionMap_id):
        self.id = id
        self.transactionMappingName = transactionMappingName
        self.transactionMapping = transactionMapping
        self.ledgerKey = ledgerKey
        self.transactionMap_id = transactionMap_id
        
    def __repr__(self):
        return '<id %r> <name %r>' % (self.id, self.transactionMappingName)

    

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
