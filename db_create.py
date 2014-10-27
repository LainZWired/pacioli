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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from pacioli import db
from pacioli import models

db.drop_all()
db.create_all()

asset_entry =  models.AccountTypes(name = 'Asset')
db.session.add(asset_entry)
liability_entry =  models.AccountTypes(name = 'Liability')
db.session.add(liability_entry)
equity_entry =  models.AccountTypes(name = 'Equity')
db.session.add(equity_entry)
revenue_entry =  models.AccountTypes(name = 'Revenue')
db.session.add(revenue_entry)
expense_entry =  models.AccountTypes(name = 'Expense')
db.session.add(expense_entry)
db.session.commit()

asset_entry =  models.Accounts(name = 'Asset', parent = 'Asset')
db.session.add(asset_entry)
bitcoins_entry =  models.Accounts(name = 'Bitcoins', parent = 'Asset')
db.session.add(bitcoins_entry)
liability_entry =  models.Accounts(name = 'Liability', parent = 'Liability')
db.session.add(liability_entry)
equity_entry =  models.Accounts(name = 'Equity', parent = 'Equity')
db.session.add(equity_entry)
revenue_entry =  models.Accounts(name = 'Revenue', parent = 'Revenue')
db.session.add(revenue_entry)
expense_entry =  models.Accounts(name = 'Expense', parent = 'Expense')
db.session.add(expense_entry)
db.session.commit()
