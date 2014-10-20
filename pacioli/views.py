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

from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from pacioli import app, db, forms, models
import io
import uuid
import os
import pacioli.memoranda
import ast
import pacioli.ledgers as ledgers
import csv
import sqlalchemy
from sqlalchemy.sql import func
from datetime import datetime

@app.route('/')
def index():
  return render_template("index.html")

@app.route('/Upload', methods=['POST','GET'])
def upload():
  filenames = ''
  if request.method == 'POST':
    uploaded_files = request.files.getlist("file[]")
    for file in uploaded_files:
      pacioli.memoranda.process(file)
    return redirect(url_for('upload'))
  memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
  
  return render_template('upload.html',
    title = 'Upload',
    memos=memos)

@app.route('/Memoranda', methods=['POST','GET'])
def memoranda():
  memos = models.Memoranda.query.order_by(models.Memoranda.date.desc()).all()
  for memo in memos:
    transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
    memo.count = len(transactions)

  return render_template('memoranda.html',
    title = 'Memoranda',
    memos=memos)
    
@app.route('/Memoranda/Delete/<fileName>')
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
  return redirect(url_for('memoranda'))

@app.route('/Memoranda/<fileName>')
def memo_file(fileName):
  memo = models.Memoranda.query.filter_by(fileName=fileName).first()
  fileText = memo.file.decode('UTF-8')
  document = io.StringIO(fileText)
  reader = csv.reader(document)
  rows = [pair for pair in reader]
  return render_template('memoFile.html',
    title = 'Memo',
    rows=rows,
    fileName=fileName)
  
@app.route('/Memoranda/Transactions')
def transactions():
  transactions = models.MemorandaTransactions.query.all()
  for transaction in transactions:
    transaction.details = ast.literal_eval(transaction.details)
    journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
    transaction.journal_entry_id = journal_entry.id
  return render_template('memoTransactions.html',
    title = 'Memo',
    transactions=transactions)


@app.route('/Memoranda/<fileName>/Transactions')
def memo_transactions(fileName):
  memo = models.Memoranda.query.filter_by(fileName=fileName).first()
  transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
  for transaction in transactions:
    transaction.details = ast.literal_eval(transaction.details)
    journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
    transaction.journal_entry_id = journal_entry.id
  return render_template('memoTransactions.html',
    title = 'Memo',
    transactions=transactions,
    fileName=fileName)

@app.route('/GeneralJournal')
def general_journal():
  entries = models.LedgerEntries.query.\
  order_by(models.LedgerEntries.date.desc()).\
  order_by(models.LedgerEntries.entryType.desc()).all()
  return render_template('generalJournal.html',
    title = 'General Journal',
    entries=entries)

@app.route('/GeneralJournal/<id>')
def journal_entry(id):
  journal_entry = journal_entry = models.JournalEntries.query.filter_by(id = id).first()
  ledger_entries = models.LedgerEntries.query.filter_by(journal_entry_id = id).order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.entryType.desc()).all()
  transaction = models.MemorandaTransactions.query.filter_by(id=journal_entry.memoranda_transactions_id).first()
  memo = models.Memoranda.query.filter_by(id=transaction.memoranda_id).first()
  transaction.details = ast.literal_eval(transaction.details)
  return render_template('journalEntry.html',
    title = 'Journal Entry',
    journal_entry=journal_entry,
    ledger_entries=ledger_entries,
    transaction=transaction,
    memo=memo)

@app.route('/GeneralLedger')
def general_ledger():
  accountsQuery = db.session.query(models.LedgerEntries.account).group_by(models.LedgerEntries.account).all()
  accounts = []
  for accountResult in accountsQuery:
    accountName = accountResult[0]
    query = ledgers.query_entries(accountName, 'Monthly')
    accounts.append(query)
  return render_template('generalLedger.html',
    title = 'General Ledger',
    accounts=accounts)

@app.route('/Ledger/<accountName>/<groupby>')
def ledger(accountName, groupby):
  query = ledgers.query_entries(accountName, groupby)
  return render_template('ledger.html',
    title = 'Ledger',
    account=query[0],
    ledger_entries=query[1],
    groupby = groupby,
    accountName=accountName)

@app.route('/Ledger/<accountName>/<groupby>/<interval>')
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
    print(interval)
    return render_template('ledger.html',
      title = 'Ledger',
      account=account,
      ledger_entries=ledger_entries,
      groupby2 = groupby,
      groupby = 'All',
      accountName=accountName,
      interval=interval)
