#!venv/bin/python
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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF liabilities, WHETHER IN CONTRACT, STRICT liabilities, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from pacioli import db
from pacioli import models
import pacioli.accounting.rates as rates

db.drop_all()
db.create_all()

db.session.add(models.Elements(name = 'Assets'))
db.session.add(models.Elements(name = 'Liabilities'))
db.session.add(models.Elements(name = 'Revenues'))
db.session.add(models.Elements(name = 'Expenses'))
db.session.add(models.Elements(name = 'Capital'))
db.session.commit()

assets_entry =  models.Classifications(name = 'Current Assets', parent = 'Assets')
db.session.add(assets_entry)
liabilities_entry =  models.Classifications(name = 'Current Liabilities', parent = 'Liabilities')
db.session.add(liabilities_entry)
equity_entry =  models.Classifications(name = "Stockholders' Equity", parent = 'Capital')
db.session.add(equity_entry)
revenues_entry =  models.Classifications(name = 'Revenues', parent = 'Revenues')
db.session.add(revenues_entry)
expenses_entry =  models.Classifications(name = 'Expenses', parent = 'Expenses')
db.session.add(expenses_entry)
gains_entry =  models.Classifications(name = 'Gains', parent = 'Revenues')
db.session.add(gains_entry)
losses_entry =  models.Classifications(name = 'Losses', parent = 'Expenses')
db.session.add(losses_entry)
db.session.commit()

assets_entry =  models.Accounts(name = 'Bitcoins', parent = 'Current Assets')
db.session.add(assets_entry)
assets_entry =  models.Accounts(name = 'Accounts Receivable', parent = 'Current Assets')
db.session.add(assets_entry)
liabilities_entry =  models.Accounts(name = 'Accounts Payable', parent = 'Current Liabilities')
db.session.add(liabilities_entry)
equity_entry =  models.Accounts(name = 'Common Stock', parent = "Stockholders' Equity")
db.session.add(equity_entry)
equity_entry =  models.Accounts(name = 'Retained Earnings', parent = "Stockholders' Equity")
db.session.add(equity_entry)
revenues_entry =  models.Accounts(name = 'Service Revenues', parent = 'Revenues')
db.session.add(revenues_entry)
revenues_entry =  models.Accounts(name = 'Revenues', parent = 'Revenues')
db.session.add(revenues_entry)
expenses_entry =  models.Accounts(name = 'Expenses', parent = 'Expenses')
db.session.add(expenses_entry)
expenses_entry =  models.Accounts(name = 'Rent Expense', parent = 'Expenses')
db.session.add(expenses_entry)
gains_entry =  models.Accounts(name = 'Asset Sale Gains', parent = 'Gains')
db.session.add(gains_entry)
losses_entry =  models.Accounts(name = 'Asset Sale Losses', parent = 'Losses')
db.session.add(losses_entry)
db.session.commit()

assets_entry =  models.Subaccounts(name = 'Coinbase', cash='investing', parent = 'Bitcoins')
db.session.add(assets_entry)
assets_entry =  models.Subaccounts(name = 'MultiBit', cash='investing', parent = 'Bitcoins')
db.session.add(assets_entry)
assets_entry =  models.Subaccounts(name = 'Bitcoin Core', cash='investing', parent = 'Bitcoins')
db.session.add(assets_entry)
assets_entry =  models.Subaccounts(name = 'Electrum', cash='investing', parent = 'Bitcoins')
db.session.add(assets_entry)
assets_entry =  models.Subaccounts(name = 'Armory', cash='investing', parent = 'Bitcoins')
db.session.add(assets_entry)
assets_entry =  models.Subaccounts(name = 'Accounts Receivable', cash='investing', parent = 'Accounts Receivable')
db.session.add(assets_entry)
liabilities_entry =  models.Subaccounts(name = 'Accounts Payable', cash='operating', parent = 'Accounts Payable')
db.session.add(liabilities_entry)
equity_entry =  models.Subaccounts(name = 'Common Stock', cash='financing', parent = "Common Stock")
db.session.add(equity_entry)
revenues_entry =  models.Subaccounts(name = 'Revenues', cash='operating', parent = 'Revenues')
db.session.add(revenues_entry)
revenues_entry =  models.Subaccounts(name = 'Salary', cash='operating', parent = 'Service Revenues')
db.session.add(revenues_entry)
expenses_entry =  models.Subaccounts(name = 'Rent Expense', cash='operating', parent = 'Rent Expense')
db.session.add(expenses_entry)
expenses_entry =  models.Subaccounts(name = 'Expenses', cash='operating', parent = 'Expenses')
db.session.add(expenses_entry)
gains_entry =  models.Subaccounts(name = 'Gains from the Sale of Bitcoins', cash='investing', parent = 'Asset Sale Gains')
db.session.add(gains_entry)
losses_entry =  models.Subaccounts(name = 'Losses from the Sale of Bitcoins', cash='investing', parent = 'Asset Sale Losses')
db.session.add(losses_entry)
db.session.commit()

usd_entry =  models.Currencies(currency = 'USD')
db.session.add(usd_entry)
db.session.commit()

btc_entry = models.Currencies(currency = 'Satoshis')
db.session.add(btc_entry)
db.session.commit()

rates.import_rates("pacioli")
