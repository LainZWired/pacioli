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

import os
import io
import uuid
import ast
import csv
import calendar
from isoweek import Week
from datetime import datetime, date, timedelta
from collections import OrderedDict
from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file, Blueprint, abort
from pacioli import app, db, forms, models
from flask_wtf import Form
import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from wtforms.ext.sqlalchemy.orm import model_form
from pacioli.accounting.memoranda import process_filestorage
import pacioli.accounting.ledgers as ledgers
import pacioli.accounting.rates as rates
import pacioli.accounting.valuations as valuations
import pacioli.treasury.treasury as treasury_functions
from decimal import Decimal

bookkeeping_blueprint = Blueprint('financial_statements', __name__,
template_folder='templates')

@financial_statements_blueprint.route('/')
def financial_statements():
    return redirect(url_for('financial_statements.income_statement', currency='Satoshis', period='Current'))

@financial_statements_blueprint.route('/IncomeStatement/<currency>/<period>')
def income_statement(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    
    if period == 'Current':
        period = datetime.now()
    else:
        period = datetime.strptime(period, "%Y-%m")
    lastday = calendar.monthrange(period.year, period.month)[1]
    year = period.year
    month = period.month
    period = datetime(year, month, lastday, 23, 59, 59)
    
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()
    net_income = 0
    for element in elements:
        element.classifications = [c for c in element.classifications if c.name in ['Revenues', 'Expenses', 'Gains', 'Losses']]
        for classification in element.classifications:
            for account in classification.accounts:
                for subaccount in account.subaccounts:
                    subaccount.total = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if period_beg <= c.date <= period_end ]
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            net_income += ledger_entry.credit
                            subaccount.total += ledger_entry.credit
                            net_income -= ledger_entry.debit
                            subaccount.total -= ledger_entry.debit
    return render_template('income_statement.html',
            title = 'Income Statement',
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income,
            period=period)

@financial_statements_blueprint.route('/BalanceSheet/<currency>/<period>')
def balance_sheet(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    
    if period == 'Current':
        period = datetime.now()
    else:
        period = datetime.strptime(period, "%Y-%m")
    lastday = calendar.monthrange(period.year, period.month)[1]
    year = period.year
    month = period.month
    period = datetime(year, month, lastday, 23, 59, 59)
    
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()

    retained_earnings = 0

    for element in elements:
        element.balance = 0
        for classification in element.classifications:
            classification.balance = 0
            for account in classification.accounts:
                account.balance = 0
                for subaccount in account.subaccounts:
                    subaccount.balance = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if c.date <= period_end ]
                    for entry in subaccount.ledgerentries:
                        if entry.currency == currency:
                            element.balance -= entry.credit
                            classification.balance -= entry.credit
                            account.balance -= entry.credit
                            subaccount.balance -= entry.credit
                            element.balance += entry.debit
                            classification.balance += entry.debit
                            account.balance += entry.debit
                            subaccount.balance += entry.debit
        if element.name == 'Equity':
            retained_earnings =  -element.balance
    elements = [c for c in elements if c.name in ['Assets', 'Liabilities']]
    return render_template('balance_sheet.html', 
    periods=periods,
    currency=currency,
    elements=elements,
    retained_earnings=retained_earnings,
    period=period_end)

@financial_statements_blueprint.route('/StatementOfCashFlows/<currency>/<period>')
def statement_of_cash_flows(currency, period):
    periods = db.session \
        .query(\
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .group_by( \
            func.date_part('year', models.LedgerEntries.date), \
            func.date_part('month', models.LedgerEntries.date)) \
        .all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    if period == 'Current':
        period = datetime.now()
        lastday = period.day
    else:
        period = datetime.strptime(period, "%Y-%m")
        lastday = calendar.monthrange(period.year, period.month)[1]
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

    elements = db.session \
        .query(models.Elements) \
        .join(models.Classifications) \
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .join(models.Accounts) \
        .join(models.Subaccounts) \
        .all()
    net_income = 0
    for element in elements:
        element.classifications = [c for c in element.classifications if c.name in ['Revenues', 'Expenses', 'Gains', 'Losses']]
        for classification in element.classifications:
            classification.balance = 0
            for account in classification.accounts:
                account.balance = 0
                for subaccount in account.subaccounts:
                    subaccount.balance = 0
                    subaccount.ledgerentries = [c for c in subaccount.ledgerentries if period_beg <= c.date <= period_end ]
                    for entry in subaccount.ledgerentries:
                        if entry.currency == currency:
                            classification.balance -= entry.credit
                            account.balance -= entry.credit
                            subaccount.balance -= entry.credit
                            classification.balance += entry.debit
                            account.balance += entry.debit
                            subaccount.balance += entry.debit
    return render_template('statement_of_cash_flows.html',
            period = period,
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income)
