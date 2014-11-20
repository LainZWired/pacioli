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
    filename = db.Column(db.Text, unique=True)
    filetype = db.Column(db.Text)
    filesize = db.Column(BigInteger)
    filetext = db.Column(db.Text)
    transactions = db.relationship('MemorandaTransactions',  backref='memo', lazy='select', cascade="save-update, merge, delete")

class MemorandaTransactions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    txid = db.Column(db.Text)
    details = db.Column(JSON)
    memoranda_id = db.Column(db.Text, db.ForeignKey('memoranda.id'))
    journal_entry = db.relationship('JournalEntries', backref='transaction', lazy='select', cascade="save-update, merge, delete")
    bitcoin_transaction = db.relationship('BitcoinTransactions', backref='transaction', lazy='select', cascade="save-update, merge, delete")

class BitcoinTransactions(db.Model):
    # txid of the bitcoins received (utxo)
    txid = db.Column(db.Text, primary_key=True)
    # output index of the bitcoins received
    vout_index = db.Column(db.Integer, primary_key=True)
    # address the bitcoins were received with
    vout_address = db.Column(db.Text)
    amount = db.Column(BigInteger)
    unspent = db.Column(db.Boolean)
    time = db.Column(db.DateTime)
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
    subaccounts = db.relationship('Subaccounts', backref='account', lazy='select', cascade="save-update, merge, delete")
    
    def __repr__(self):
        return self.name

class Subaccounts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    parent = db.Column(db.Text, db.ForeignKey('accounts.name'))
    cash = db.Column(db.Text)
    ledgerentries = db.relationship('LedgerEntries', backref='subaccount', lazy='select', cascade="save-update, merge, delete", order_by="LedgerEntries.date")

    def __repr__(self):
        return self.name

class JournalEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    memoranda_transactions_id = db.Column(db.Text, db.ForeignKey('memoranda_transactions.id'))
    ledgerentries = db.relationship('LedgerEntries', backref='journalentry', lazy='select', cascade="save-update, merge, delete", order_by="desc(LedgerEntries.debit), desc(LedgerEntries.credit)")
    sales_invoices = db.relationship('SalesInvoices', backref='JournalEntry', lazy='select', cascade="save-update, merge, delete")
    
class LedgerEntries(db.Model):
    id = db.Column(db.Text, primary_key=True)
    date = db.Column(db.DateTime)
    debit = db.Column(db.Numeric)
    credit = db.Column(db.Numeric)
    currency = db.Column(db.Text, db.ForeignKey('currencies.currency'))
    ledger = db.Column(db.Text, db.ForeignKey('subaccounts.name'))
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))

class Identities(db.Model):
    id = db.Column(db.Text, primary_key=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    irc_nick = db.Column(db.Text, unique=True)
    email = db.Column(db.Text, unique=True)
    fingerprint = db.Column(db.Text)
    rating = db.Column(db.Numeric)
    rating_comment = db.Column(db.Text)
    credit_limit = db.Column(db.Numeric)
    sales_orders = db.relationship('SalesOrders', backref='Identity', lazy='select', cascade="save-update, merge, delete")
    purchase_orders = db.relationship('PurchaseOrders', backref='Identity', lazy='select', cascade="save-update, merge, delete")

class SalesOrders(db.Model):
    id = db.Column(db.Text, primary_key=True)
    received_date = db.Column(db.DateTime)
    approved_date = db.Column(db.DateTime)
    items_shipped_date = db.Column(db.DateTime)
    sales_invoices = db.relationship('SalesInvoices', backref='SalesOrder', lazy='select', cascade="save-update, merge, delete")
    items = db.relationship('SalesOrderItems', backref='SalesOrder', lazy='select', cascade="save-update, merge, delete")
    customer_id = db.Column(db.Text, db.ForeignKey('identities.id'))

class SalesOrderItems(db.Model):
    id = db.Column(db.Text, primary_key=True)
    unit_price = db.Column(db.Numeric)
    quantity_shipped = db.Column(db.Numeric)
    quantity_ordered = db.Column(db.Numeric)
    currency = db.Column(db.Text, db.ForeignKey('currencies.currency'))
    item = db.Column(db.Text, db.ForeignKey('items.name'))
    sales_order_id = db.Column(db.Text, db.ForeignKey('sales_orders.id'))

class SalesInvoices(db.Model):
    id = db.Column(db.Text, primary_key=True)
    sent_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    bitcoin_address = db.Column(db.Text)
    sales_order_id = db.Column(db.Text, db.ForeignKey('sales_orders.id'))
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))

class PurchaseOrders(db.Model):
    id = db.Column(db.Text, primary_key=True)
    sent_date = db.Column(db.DateTime)
    approved_date = db.Column(db.DateTime)
    items_received_date = db.Column(db.DateTime)
    purchase_invoices = db.relationship('PurchaseInvoices', backref='PurchaseOrder', lazy='select', cascade="save-update, merge, delete")
    items = db.relationship('PurchaseOrderItems', backref='PurchaseOrder', lazy='select', cascade="save-update, merge, delete")
    vendor_id = db.Column(db.Text, db.ForeignKey('identities.id'))

class PurchaseOrderItems(db.Model):
    id = db.Column(db.Text, primary_key=True)
    unit_price = db.Column(db.Numeric)
    quantity_ordered = db.Column(db.Numeric)
    quantity_received = db.Column(db.Numeric)
    currency = db.Column(db.Text, db.ForeignKey('currencies.currency'))
    item = db.Column(db.Text, db.ForeignKey('items.name'))
    purchase_order_id = db.Column(db.Text, db.ForeignKey('purchase_orders.id'))

class PurchaseInvoices(db.Model):
    id = db.Column(db.Text, primary_key=True)
    received_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    bitcoin_address = db.Column(db.Text)
    purchase_order_id = db.Column(db.Text, db.ForeignKey('purchase_orders.id'))
    journal_entry_id = db.Column(db.Text, db.ForeignKey('journal_entries.id'))

class Items(db.Model):
    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, unique=True)
    description = db.Column(db.Text, unique=True)
    items_sold = db.relationship('SalesOrderItems', backref='Item', lazy='select', cascade="save-update, merge, delete")
    items_purchased = db.relationship('PurchaseOrderItems', backref='Item', lazy='select', cascade="save-update, merge, delete")
    def __repr__(self):
        return self.name

    
class Currencies(db.Model):
    currency = db.Column(db.Text, primary_key=True)

class PriceFeeds(db.Model):
    price_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.BigInteger)
    price = db.Column(db.Numeric)
    volume = db.Column(db.Numeric)

class Rates(db.Model):
    date = db.Column(db.BigInteger, primary_key=True)
    source = db.Column(db.Text)
    currency = db.Column(db.Text, db.ForeignKey('currencies.currency'))
    rate = db.Column(db.Numeric)
