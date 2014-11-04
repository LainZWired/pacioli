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

from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from pacioli import app, db, forms, models
import io
import uuid
import os
import pacioli.memoranda
import ast
import pacioli.ledgers as ledgers
import pacioli.prices as prices
import csv
import sqlalchemy
from sqlalchemy.sql import func
from datetime import datetime,date
import calendar
from collections import OrderedDict

@app.route('/')
def index():
    return render_template("index.html")
  
@app.route('/Configure')
def configure():
    return render_template("configure/configure.html")
  
@app.route('/Configure/SummarizePrices')
def summarize_prices():
    prices.summarize_data("pacioli")
    return redirect(url_for('configure'))
    
@app.route('/Configure/ImportPrices')
def import_prices():
    prices.import_summary("pacioli")
    return redirect(url_for('configure'))
  
@app.route('/Configure/ChartOfAccounts', methods=['POST','GET'])
def chart_of_accounts():
    form = forms.NewAccount()
    accounts = models.Accounts.query.order_by(models.Accounts.parent).all()
    if request.method == 'POST':
        name = form.account.data
        parent = form.accounttype.data
        parent = parent.name
        account = models.Accounts(name=name, parent=parent)
        db.session.add(account)
        db.session.commit()
        return redirect(url_for('chart_of_accounts'))
    return render_template("configure/chart_of_accounts.html",
    accounts=accounts,
    form=form)

@app.route('/Configure/ChartOfAccounts/Delete/<account>')
def delete_account(account):
    findaccount = models.Accounts.query.filter_by(name=account).first()
    db.session.delete(findaccount)
    db.session.commit()
    return redirect(url_for('chart_of_accounts'))

@app.route('/Bookkeeping')
def bookkeeping():
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Upload', methods=['POST','GET'])
def upload_csv():
    filenames = ''
    if request.method == 'POST':
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            pacioli.memoranda.process_filestorage(file)
        return redirect(url_for('upload_csv'))
    memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
    return render_template('bookkeeping/upload.html',
        title = 'Upload',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/Delete/<fileName>')
def delete_memoranda(fileName):
    memo = models.Memoranda.query.filter_by(fileName=fileName).first()
    transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
    for transaction in transactions:
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = journal_entry.id).all()
        for entry in ledger_entries:
            db.session.delete(entry)
            db.session.commit()
        db.session.delete(journal_entry)
        db.session.commit()
        db.session.delete(transaction)
        db.session.commit()
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for('upload_csv'))

@app.route('/Bookkeeping/Memoranda', methods=['POST','GET'])
def memoranda():
    memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
    for memo in memos:
        transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
        memo.count = len(transactions)

    return render_template('bookkeeping/memoranda.html',
        title = 'Memoranda',
        memos=memos)

@app.route('/Bookkeeping/Memoranda/<fileName>')
def memo_file(fileName):
    memo = models.Memoranda.query.filter_by(fileName=fileName).first()
    fileText = memo.fileText
    document = io.StringIO(fileText)
    reader = csv.reader(document)
    rows = [pair for pair in reader]
    return render_template('bookkeeping/memo_file.html',
        title = 'Memo',
        rows=rows,
        fileName=fileName)
  
@app.route('/Bookkeeping/Memoranda/Transactions')
def transactions():
    transactions = models.MemorandaTransactions.query.all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions)


@app.route('/Bookkeeping/Memoranda/<fileName>/Transactions')
def memo_transactions(fileName):
    memo = models.Memoranda.query.filter_by(fileName=fileName).first()
    transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('bookkeeping/memo_transactions.html',
        title = 'Memo',
        transactions=transactions,
        fileName=fileName)

@app.route('/Bookkeeping/GeneralJournal')
def general_journal():
    entries = models.LedgerEntries.query.\
    order_by(models.LedgerEntries.date.desc()).\
    order_by(models.LedgerEntries.journal_entry_id.desc()).\
    order_by(models.LedgerEntries.entryType.desc()).all()
    return render_template('bookkeeping/general_journal.html',
        title = 'General Journal',
        entries=entries)

@app.route('/Bookkeeping/GeneralJournal/<id>')
def journal_entry(id):
    journal_entry = models.JournalEntries.query.filter_by(id = id).first()
    ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = id).order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.entryType.desc()).all()
    transaction = models.MemorandaTransactions.query.filter_by(id=journal_entry.memoranda_transactions_id).first()
    memo = models.Memoranda.query.filter_by(id=transaction.memoranda_id).first()
    transaction.details = ast.literal_eval(transaction.details)
    return render_template('bookkeeping/journal_entry.html',
        title = 'Journal Entry',
        journal_entry=journal_entry,
        ledger_entries=ledger_entries,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralJournal/<id>/Edit', methods=['POST','GET'])
def edit_journal_entry(id):
    journal_entry = models.JournalEntries.query.filter_by(id = id).first()
    ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = id).order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.entryType.desc()).all()
    transaction = models.MemorandaTransactions.query.filter_by(id=journal_entry.memoranda_transactions_id).first()
    memo = models.Memoranda.query.filter_by(id=transaction.memoranda_id).first()
    transaction.details = ast.literal_eval(transaction.details)
    return render_template('bookkeeping/journal_entry_edit.html',
        title = 'Journal Entry',
        journal_entry=journal_entry,
        ledger_entries=ledger_entries,
        transaction=transaction,
        memo=memo)

@app.route('/Bookkeeping/GeneralLedger')
def general_ledger():
    accountsQuery = db.session.query(models.LedgerEntries.account).group_by(models.LedgerEntries.account).all()
    accounts = []
    for accountResult in accountsQuery:
        accountName = accountResult[0]
        query = ledgers.query_entries(accountName, 'Monthly')
        accounts.append(query)
    return render_template('bookkeeping/general_ledger.html',
        title = 'General Ledger',
        accounts=accounts)

@app.route('/Bookkeeping/Ledger/<accountName>/<groupby>')
def ledger(accountName, groupby):
    query = ledgers.query_entries(accountName, groupby)
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        account=query[0],
        ledger_entries=query[1],
        groupby = groupby,
        accountName=accountName)

@app.route('/Bookkeeping/Ledger/<accountName>/<groupby>/<interval>')
def ledger_page(accountName, groupby, interval):
    if groupby == "Daily":
        interval = datetime.strptime(interval, "%m-%d-%Y")
        year = interval.year
        month = interval.month
        day = interval.day
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month, func.date_part('day', models.LedgerEntries.date)==day).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.asc()).all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    if groupby == "Monthly":
        interval = datetime.strptime(interval, "%m-%Y")
        year = interval.year
        month = interval.month
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.desc()).all()
        account = ledgers.foot_account(accountName, ledger_entries, 'All')
    return render_template('bookkeeping/ledger.html',
        title = 'Ledger',
        account=account,
        ledger_entries=ledger_entries,
        groupby2 = groupby,
        groupby = 'All',
        accountName=accountName,
        interval=interval)

@app.route('/Bookkeeping/TrialBalance')
def trial_balance():
    accountsQuery = db.session.query(models.LedgerEntries.account).group_by(models.LedgerEntries.account).all()
    periods = db.session.query(\
        func.date_part('year', models.LedgerEntries.date) + '-'+
        func.date_part('month', models.LedgerEntries.date)).\
      group_by(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)).all()
    period = datetime.now()    
    year = period.year
    month = period.month
    accounts = []
    for accountResult in accountsQuery:
        accountName = accountResult[0]
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.desc()).all()
        query = ledgers.foot_account(accountName, ledger_entries, 'All')
        accounts.append(query)
    return render_template('bookkeeping/trial_balance.html', periods=periods, period=period, accounts=accounts)

@app.route('/Bookkeeping/TrialBalance/<groupby>/<period>')
def trial_balance_historical(groupby, period):
    accountsQuery = db.session.query(models.LedgerEntries.account).group_by(models.LedgerEntries.account).all()
    periods = db.session.query(\
        func.date_part('year', models.LedgerEntries.date) + '-'+
        func.date_part('month', models.LedgerEntries.date)).\
      group_by(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)).all()
    period = datetime.strptime(period, "%Y-%m")
    year = period.year
    month = period.month
    day = calendar.monthrange(year, month)[1]
    period = datetime(year, month, day, 23, 59, 59)
    accounts = []
    totalDebits = 0
    totalCredits = 0
    for accountResult in accountsQuery:
        accountName = accountResult[0]
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.desc()).all()
        query = ledgers.foot_account(accountName, ledger_entries, 'All')
        totalDebits += query['debitBalance']
        totalCredits += query['creditBalance']
        accounts.append(query)
    return render_template('bookkeeping/trial_balance.html', periods=periods, period=period, accounts=accounts, totalDebits=totalDebits, totalCredits=totalCredits)


@app.route('/FinancialStatements')
def financial_statements():
    return redirect(url_for('income_statement', currency='Dollars'))


@app.route('/FinancialStatements/IncomeStatement/<currency>')
def income_statement(currency):
    periods = db.session.query(\
      func.date_part('year', models.LedgerEntries.date),\
      func.date_part('month', models.LedgerEntries.date)).\
      group_by(func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)\
      ).all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    period = datetime.now()
    period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0)
    period_end = datetime(period.year, period.month, period.day, 23, 59, 59, 999999)

    entries = db.session\
        .query(models.LedgerEntries)\
        .join(models.Accounts)\
        .join(models.Classifications)\
        .filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses']))\
        .filter(models.LedgerEntries.date.between(period_beg, period_end))\
        .all()
    response = {}
    response['Net Income'] = 0
    classifications = models.Classifications.query.filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses'])).all()
    accounts = models.Accounts.query.filter(models.Classifications.name.in_(['Revenues', 'Expenses', 'Gains', 'Losses'])).all()
    for classification in classifications:
        print(classification.name)
        response[classification.name] = {}
    for account in accounts:
        classification = account.classification.name
        response[classification][account.name] = 0
    for entry in entries:
        account = entry.account.name
        classification = entry.account.classification.name
        if entry.tside == 'debit':
            response[classification][account] += entry.amount
        elif entry.tside == 'credit':
            response[classification][account] -= entry.amount
        if entry.account.classification.element.name is 'Revenues' or 'Gains':
            response['Net Income'] += entry.amount
        elif entry.account.classification.element.name is 'Expenses' or 'Losses':
            response['Net Income'] -= entry.amount
    gain = ledger.get_fifo_realized_gain(Bitcoins, period_beg, period_end)
    ungain = ledger.get_fifo_unrealized_gain(Bitcoins, period_end)
    response['Gains'] = gain
    response['Net Income'] += gain
    response['Unrealized Gain'] += ungain
    print(response)
    return render_template('financial_statements/income_statement.html',
            title = 'Income Statement',
            periods = periods,
            response = response)
    
@app.route('/FinancialStatements/IncomeStatement/<period>')
def income_statement_historical(period):
    lastday = calendar.monthrange(period.year, period.month)[1]

    periods = db.session.query(\
      func.date_part('year', models.LedgerEntries.date),\
      func.date_part('month', models.LedgerEntries.date)).\
      group_by(func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)\
      ).all()
    periods = sorted([date(int(period[0]), int(period[1]), 1) for period in periods])
    accounts = db.session.query(models.Accounts).filter(models.Accounts.parent.in_(['Revenues', 'Expenses'])).all()
    elements = (('Revenues', {}), ('Expenses',{}),( 'Net Income', {}))
    elements = OrderedDict(elements)
    for account in accounts:
        for period in periods:
            query = db.session.query(\
              func.sum(models.LedgerEntries.amount)).\
              filter_by(
                account=account).\
              group_by(\
                func.date_part('year', models.LedgerEntries.date),
                func.date_part('month', models.LedgerEntries.date)).\
              having(func.date_part('year', models.LedgerEntries.date)==period.year).\
              having(func.date_part('month', models.LedgerEntries.date)==period.month).\
                all()
            if query == []:
                query = [[(0)]]
            accounts[account_name][period] = int(query[0][0])
        accounts[account_name] = OrderedDict(sorted(accounts[account_name].items()))
    for period in periods:
        net = accounts['Revenues'][period] - accounts['Expenses'][period]
        accounts['Net Income'][period] = net
        accounts['Net Income'] = OrderedDict(sorted(accounts['Net Income'].items()))
    return render_template('financial_statements/income_statement.html',
            title = 'Income Statement',
            periods = periods,
            accounts = accounts)
    
@app.route('/FinancialStatements/BalanceSheet')
def balance_sheet():
    periods = db.session.query(\
        func.date_part('year', models.LedgerEntries.date) + '-'+
        func.date_part('month', models.LedgerEntries.date)).\
      group_by(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)).all()
    elements = db.session.query(models.Elements).all()
    classifications = db.session.query(models.Classifications).all()
    accounts = db.session.query(models.Accounts).all()
    period = datetime.now()    
    year = period.year
    month = period.month
    balances = []
    for account in accounts:
        accountName = account.name
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.desc()).all()
        query = ledgers.foot_account(accountName, ledger_entries, 'All')
        balances.append(query)
    return render_template('financial_statements/balance_sheet.html', period=period, periods=periods, elements=elements, classifications=classifications, accounts=accounts, balances=balances)
    
@app.route('/FinancialStatements/BalanceSheet/<period>')
def balance_sheet_historical(period):
    periods = db.session.query(\
        func.date_part('year', models.LedgerEntries.date) + '-'+
        func.date_part('month', models.LedgerEntries.date)).\
      group_by(\
        func.date_part('year', models.LedgerEntries.date),\
        func.date_part('month', models.LedgerEntries.date)).all()
    elements = db.session.query(models.Elements).all()
    classifications = db.session.query(models.Classifications).all()
    accounts = db.session.query(models.Accounts).all()
    period = datetime.strptime(period, "%Y-%m")
    year = period.year
    month = period.month
    day = calendar.monthrange(year, month)[1]
    period = datetime(year, month, day, 23, 59, 59)
    balances = []
    for account in accounts:
        accountName = account.name
        ledger_entries = models.LedgerEntries.query.\
          filter_by(account=accountName).\
          filter( func.date_part('year', models.LedgerEntries.date)==year, func.date_part('month', models.LedgerEntries.date)==month).\
          order_by(models.LedgerEntries.date).\
          order_by(models.LedgerEntries.entryType.desc()).all()
        balance = ledgers.get_balance(accountName, period)
        balances.append(balance)
    return render_template('financial_statements/balance_sheet.html', period=period, periods=periods, elements=elements, classifications=classifications, accounts=accounts, balances=balances)
    
@app.route('/FinancialStatements/StatementOfCashFlows')
def statement_of_cash_flows():
    return render_template('financial_statements/statement_of_cash_flows.html')
    
