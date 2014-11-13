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
from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
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

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/Configure')
def configure():
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts')
def chart_of_accounts():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    return render_template("configure/chart_of_accounts.html",
        subaccounts=subaccounts,
        classificationform=classificationform,
        accountform=accountform,
        subaccountform=subaccountform)

@app.route('/Configure/ChartOfAccounts/AddClassification', methods=['POST','GET'])
def add_classification():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['classification']
        parent = form['classificationparent']
        parent = models.Elements.query.filter_by(id=parent).one()
        parent = parent.name
        classification = models.Classifications(name=name, parent=parent)
        db.session.add(classification)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteClassification/<classification>')
def delete_classification(classification):
    classification = models.Classifications \
        .query \
        .filter_by(name=classification) \
        .first()
    db.session.delete(classification)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/AddAccount', methods=['POST','GET'])
def add_account():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['account']
        parent = form['accountparent']
        parent = models.Classifications \
            .query \
            .filter_by(id=parent) \
            .one()
        parent = parent.name
        account = models.Accounts(name=name, parent=parent)
        db.session.add(account)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteAccount/<account>')
def delete_account(account):
    account = models.Accounts.query.filter_by(name=account).first()
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/AddSubAccount', methods=['POST','GET'])
def add_subaccount():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['subaccount']
        parent = form['subaccountparent']
        parent = models.Accounts.query.filter_by(id=parent).one()
        parent = parent.name
        subaccount = models.Subaccounts(name=name, parent=parent)
        db.session.add(subaccount)
        db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Configure/ChartOfAccounts/DeleteSubAccount/<subaccount>')
def delete_subaccount(subaccount):
    subaccount = models.Accounts.query.filter_by(name=subaccount).first()
    db.session.delete(subaccount)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Bookkeeping')
def bookkeeping():
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Memoranda/Upload', methods=['POST','GET'])
def upload_csv():
    filenames = ''
    if request.method == 'POST':
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            process_filestorage(file)
        return redirect(url_for('upload_csv'))
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    return render_template('bookkeeping/upload.html',
        title = 'Upload',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/ExchangeRates')
def exchange_rates():
    return render_template("bookkeeping/exchange_rates.html")

@app.route('/Bookkeeping/Memoranda/DownloadRates')
def download_rates():
    rates.download_rates()
    return redirect(url_for('exchange_rates'))
  
@app.route('/Bookkeeping/Memoranda/ExchangeRates/Summarize')
def summarize_rates():
    rates.summarize_rates("pacioli")
    return redirect(url_for('exchange_rates'))
  
@app.route('/Bookkeeping/Memoranda/ExchangeRates/Import')
def import_rates():
    rates.import_rates("pacioli")
    return redirect(url_for('exchange_rates'))

@app.route('/Bookkeeping/Memoranda/ExchangeRates/CalculateGains/<method>')
def calc_gains(method):
    valuations.calculate_bitcoin_gains(method)
    return redirect(url_for('exchange_rates'))

@app.route('/Bookkeeping/Memoranda/Memos', methods=['POST','GET'])
def memoranda():
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    for memo in memos:
        transactions = models.MemorandaTransactions \
            .query \
            .filter_by(memoranda_id=memo.id) \
            .all()
        memo.count = len(transactions)

    return render_template('bookkeeping/memos.html',
        title = 'Memoranda',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/Memos/Delete/<fileName>')
def delete_memoranda(fileName):
    memo = models.Memoranda \
        .query \
        .filter_by(fileName=fileName) \
        .first()
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Memoranda/Memos/<fileName>')
def memo_file(fileName):
    memo = models.Memoranda \
        .query \
        .filter_by(fileName=fileName) \
        .first()
    fileText = memo.fileText
    document = io.StringIO(fileText)
    reader = csv.reader(document)
    rows = [pair for pair in reader]
    return render_template('bookkeeping/memo_file.html',
        title = 'Memo',
        rows=rows,
        fileName=fileName)
  
@app.route('/Bookkeeping/Memoranda/Memos/Transactions')
def transactions():
    transactions = models.MemorandaTransactions.query.all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions)


@app.route('/Bookkeeping/Memoranda/Memos/<fileName>/Transactions')
def memo_transactions(fileName):
    memo = models.Memoranda \
        .query \
        .filter_by(fileName=fileName) \
        .first()
    transactions = models.MemorandaTransactions \
        .query \
        .filter_by(memoranda_id=memo.id) \
        .all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries \
            .query \
            .filter_by(memoranda_transactions_id=transaction.id) \
            .first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions,
        fileName=fileName)

@app.route('/Bookkeeping/GeneralJournal/<currency>')
def general_journal(currency):
    journal_entries = db.session \
        .query(models.JournalEntries) \
        .filter(models.JournalEntries.ledgerentries \
            .any(currency=currency)) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .all()
    for journal_entry in journal_entries:
        journal_entry.ledgerentries = [c for c in journal_entry.ledgerentries if c.currency == currency]
    return render_template('bookkeeping/general_journal.html',
        title = 'General Journal',
        journal_entries=journal_entries,
        currency=currency)

@app.route('/Bookkeeping/GeneralJournal/Entry/<id>')
def journal_entry(id):
    journal_entry = models.JournalEntries \
        .query \
        .filter_by(id=id) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .order_by(models.LedgerEntries.tside.desc()) \
        .one()
    
    transaction = models.MemorandaTransactions \
        .query \
        .filter_by(id=journal_entry.memoranda_transactions_id) \
        .first()
    memo = models.Memoranda \
        .query \
        .filter_by(id=transaction.memoranda_id) \
        .first()
    transaction.details = ast.literal_eval(transaction.details)

    return render_template('bookkeeping/journal_entry.html',
        title = 'Journal Entry',
        journal_entry=journal_entry,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralJournal/<id>/<currency>/Edit', methods=['POST','GET'])
def edit_journal_entry(id, currency):
    
    if request.method == 'POST':
        print(request.form.copy())
        return redirect(url_for('edit_journal_entry', id=id, currency=currency))
    
    journal_entry = models.JournalEntries \
        .query \
        .filter_by(id=id) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .order_by(models.LedgerEntries.tside.desc()) \
        .one()
        
    MyForm = model_form(models.LedgerEntries, Form, exclude_fk=False)
    
    for ledger_entry in journal_entry.ledgerentries:
        if ledger_entry.currency == currency:
            ledger_entry.form = MyForm(request.form, ledger_entry)
            print(ledger_entry.form.tside)

    transaction = models.MemorandaTransactions \
        .query \
        .filter_by(id=journal_entry.memoranda_transactions_id) \
        .first()
    memo = models.Memoranda \
        .query \
        .filter_by(id=transaction.memoranda_id) \
        .first()
    transaction.details = ast.literal_eval(transaction.details)
    
    return render_template('bookkeeping/journal_entry_edit.html',
        title = 'Journal Entry',
        id=id,
        currency = currency, 
        journal_entry=journal_entry,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralLedger/<currency>')
def general_ledger(currency):
    accountsQuery = db.session\
        .query(models.LedgerEntries.ledger)\
        .group_by(models.LedgerEntries.ledger).all()
    accounts = []
    for accountResult in accountsQuery: 
        accountName = accountResult[0]
        query = ledgers.query_entries(accountName, 'Monthly', currency)
        accounts.append(query)
    return render_template('bookkeeping/general_ledger.html',
        title = 'General Ledger',
        accounts=accounts,
        currency=currency)

@app.route('/Bookkeeping/Ledger/<accountName>/<currency>/<groupby>')
def ledger(accountName, currency, groupby):
    query = ledgers.query_entries(accountName, groupby, currency)
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        currency=currency,
        account=query[0],
        ledger_entries=query[1],
        groupby = groupby,
        accountName=accountName)

@app.route('/Bookkeeping/Ledger/<accountName>/<currency>/<groupby>/<interval>')
def ledger_page(accountName, currency, groupby, interval):
    if groupby == "Daily":
        interval = datetime.strptime(interval, "%m-%d-%Y")
        year = interval.year
        month = interval.month
        day = interval.day
        ledger_entries = models.LedgerEntries \
            .query \
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter( \
                func.date_part('year', models.LedgerEntries.date)==year, \
                func.date_part('month', models.LedgerEntries.date)==month, \
                func.date_part('day', models.LedgerEntries.date)==day) \
            .order_by(models.LedgerEntries.date) \
            .order_by(models.LedgerEntries.tside.asc()) \
            .all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    if groupby == "Monthly":
        interval = datetime.strptime(interval, "%m-%Y")
        year = interval.year
        month = interval.month
        ledger_entries = models.LedgerEntries\
            .query\
            .filter_by(ledger=accountName) \
            .filter_by(currency=currency) \
            .filter( \
                func.date_part('year', models.LedgerEntries.date)==year, \
                func.date_part('month', models.LedgerEntries.date)==month)\
            .order_by(models.LedgerEntries.date) \
            .order_by(models.LedgerEntries.tside.desc()) \
            .all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        account=account,
        ledger_entries=ledger_entries,
        groupby2 = groupby,
        groupby = 'All',
        accountName=accountName,
        interval=interval,
        currency=currency)

@app.route('/Bookkeeping/TrialBalance/<currency>/<groupby>/<period>')
def trial_balance(currency, groupby, period):
    
    if groupby == 'Daily':
        periods = db.session \
            .query(\
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .order_by( \
                func.date_part('year', models.LedgerEntries.date).desc(), \
                func.date_part('month', models.LedgerEntries.date).desc(), \
                func.date_part('day', models.LedgerEntries.date).desc()) \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .limit(7)

        periods = sorted([date(int(period[0]), int(period[1]), int(period[2])) for period in periods])
        if period == 'Current':
            period = periods[-1]
        else:
            period = datetime.strptime(period, "%Y-%m-%d")
        
        period_beg = datetime(period.year, period.month, period.day, 0, 0, 0, 0)
        period_end = datetime(period.year, period.month, period.day, 23, 59, 59, 999999)
        
        periods = sorted([period.strftime("%Y-%m-%d") for period in periods])
        

    elif groupby == 'Weekly':
        periods = db.session \
            .query(\
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('week', models.LedgerEntries.date)) \
            .order_by( \
                func.date_part('year', models.LedgerEntries.date).desc(), \
                func.date_part('week', models.LedgerEntries.date).desc()) \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('week', models.LedgerEntries.date)) \
            .limit(7)
        periods = sorted([Week(int(period[0]), int(period[1])).monday() for period in periods])
        
        if period == 'Current':
            period = periods[-1]
        else:
            period = period.split('-')
            period = Week(int(period[0]), int(period[1])+1).monday()
            print(period)
            
        period_beg = period - timedelta(days = period.weekday())
        period_end = period_beg + timedelta(days = 6)
        period_beg = datetime(period_beg.year, period_beg.month, period_beg.day, 0, 0, 0, 0)
        period_end = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, 999999)
        
        periods = sorted([period.strftime("%Y-%W") for period in periods])

    elif groupby == 'Monthly':
        if period == 'Current':
            period = datetime.now()
        else:
            period = datetime.strptime(period, "%Y-%m")
        lastday = calendar.monthrange(period.year, period.month)[1]
        period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
        period_end = period = datetime(period.year, period.month, lastday, 23, 59, 59, 999999)

        periods = db.session \
            .query(\
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .group_by( \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .all()
        periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
        
    elif groupby == 'Annual':
        if period == 'Current':
            period = datetime.now()
        else:
            period = datetime.strptime(period, "%Y")
        period_beg = datetime(period.year, 1, 1, 0, 0, 0, 0)
        period_end = datetime(period.year, 12, 31, 23, 59, 59, 999999)
        
        periods = db.session \
            .query(func.date_part('year', models.LedgerEntries.date)) \
            .group_by(func.date_part('year', models.LedgerEntries.date)) \
            .all()
        periods = sorted([date(int(period[0]), 12, 31) for period in periods])
    
    print(period_beg)
    print(period_end)
    subaccounts = db.session \
        .query(models.LedgerEntries.ledger, models.LedgerEntries.tside, func.sum(models.LedgerEntries.amount)) \
        .filter(models.LedgerEntries.currency==currency) \
        .filter( models.LedgerEntries.date.between(period_beg, period_end)) \
        .group_by(models.LedgerEntries.ledger) \
        .group_by(models.LedgerEntries.tside) \
        .all()
    totalDebits = 0
    totalCredits = 0
    for subaccount in subaccounts:
        if subaccount[1] == 'debit':
            totalDebits += subaccount[2]
        if subaccount[1] == 'credit':
            totalCredits += subaccount[2]

    print(subaccounts)
    print(period)
    
    return render_template('bookkeeping/trial_balance.html',
        groupby=groupby,
        currency=currency,
        periods=periods,
        period=period,
        period_beg=period_beg,
        period_end=period_end,
        totalDebits=totalDebits,
        totalCredits=totalCredits,
        subaccounts=subaccounts)

@app.route('/FinancialStatements')
def financial_statements():
    return redirect(url_for('income_statement', currency='Satoshis', period='Current'))

@app.route('/FinancialStatements/IncomeStatement/<currency>/<period>')
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
                            if ledger_entry.tside == 'credit':
                                net_income += ledger_entry.amount
                                subaccount.total += ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                net_income -= ledger_entry.amount
                                subaccount.total -= ledger_entry.amount
    return render_template('financial_statements/income_statement.html',
            title = 'Income Statement',
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income,
            period=period)

@app.route('/FinancialStatements/BalanceSheet/<currency>/<period>')
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
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            
                            if ledger_entry.tside == 'credit':
                                element.balance -= ledger_entry.amount
                                classification.balance -= ledger_entry.amount
                                account.balance -= ledger_entry.amount
                                subaccount.balance -= ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                element.balance += ledger_entry.amount
                                classification.balance += ledger_entry.amount
                                account.balance += ledger_entry.amount
                                subaccount.balance += ledger_entry.amount
        if element.name == 'Equity':
            retained_earnings =  -element.balance
            print(retained_earnings)
    elements = [c for c in elements if c.name in ['Assets', 'Liabilities']]
    return render_template('financial_statements/balance_sheet.html', 
    periods=periods,
    currency=currency,
    elements=elements,
    retained_earnings=retained_earnings,
    period=period_end)

@app.route('/FinancialStatements/StatementOfCashFlows/<currency>/<period>')
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
                    for ledger_entry in subaccount.ledgerentries:
                        if ledger_entry.currency == currency:
                            
                            if ledger_entry.tside == 'credit':
                                classification.balance -= ledger_entry.amount
                                account.balance -= ledger_entry.amount
                                subaccount.balance -= ledger_entry.amount
                            elif ledger_entry.tside == 'debit':
                                classification.balance += ledger_entry.amount
                                account.balance += ledger_entry.amount
                                subaccount.balance += ledger_entry.amount
    return render_template('financial_statements/statement_of_cash_flows.html',
            period = period,
            periods = periods,
            currency = currency,
            elements = elements,
            net_income = net_income)
