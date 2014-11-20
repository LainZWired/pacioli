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

from flask_wtf import Form
from wtforms import TextField, TextAreaField, \
SubmitField, SelectField, FloatField, validators, BooleanField, DateTimeField, DecimalField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import Required, Length
from wtforms.ext.sqlalchemy.orm import model_form
from sqlalchemy.sql import func 
from pacioli import models, db
from pacioli.models import Elements, Classifications, Accounts, Subaccounts, LedgerEntries, Items

def available_classification_parents():
    return Elements.query

def available_account_parents():
    return Classifications.query

def available_subaccount_parents():
    return Accounts.query

def available_subaccounts():
    return Subaccounts.query

def available_items():
    return Items.query
    
class NewClassification(Form):
    classification = TextField("Classification Name")
    classificationparent = QuerySelectField(query_factory=available_classification_parents, allow_blank=False)

class NewAccount(Form):
    account = TextField("Account Name")
    accountparent = QuerySelectField(query_factory=available_account_parents, allow_blank=False)

class NewSubAccount(Form):
    subaccount = TextField("Sub-Account Name")
    subaccountparent = QuerySelectField(query_factory=available_subaccount_parents, allow_blank=False)

class EditLedgerEntry(Form):
    id = TextField('id')
    date = DateTimeField("Ledger Entry Date")
    debit = DecimalField("Debit Amount")
    credit = DecimalField("Credit Amount")
    ledger = QuerySelectField(query_factory=available_subaccounts, allow_blank=False)

class JournalEntry(Form):
    id = TextField('id')
    date = DateTimeField("Ledger Entry Date")
    amount = DecimalField("Amount")
    debit_ledger = QuerySelectField(query_factory=available_subaccounts, allow_blank=False)
    credit_ledger = QuerySelectField(query_factory=available_subaccounts, allow_blank=False)
    currency = SelectField(
                choices=[('Satoshis', 'Satoshis'),
                         ('USD', 'USD')])

class NewIdentity(Form):
    first_name = TextField("First name")
    last_name = TextField("Last name")
    irc_nick = TextField("IRC Nick")
    email = TextField("Email")
    
class NewInvoice(Form):
    amount = DecimalField("Amount")
    

class NewPurchaseOrderItem(Form):
    item = QuerySelectField(query_factory=available_items, allow_blank=False)
    unit_price = DecimalField("Unit Price")
    currency = SelectField(
                choices=[('Satoshis', 'Satoshis'),
                         ('USD', 'USD')])
    quantity_ordered = DecimalField("Quantity")
