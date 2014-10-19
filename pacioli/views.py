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

from collections import OrderedDict
from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from pacioli import app, db, forms, models
import io
import uuid
import os
import datetime
import pacioli.memoranda
import ast
import pacioli.ledgers as ledgers
import csv
from sqlalchemy.sql import func
import sqlalchemy

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
  entries = models.LedgerEntries.query.order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.entryType.desc()).all()
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
    ledger_entries = models.LedgerEntries.query.\
      filter_by(account=accountName).\
      order_by(models.LedgerEntries.date.desc()).\
      order_by(models.LedgerEntries.entryType.desc()).all()
    account = ledgers.foot_account(accountName, ledger_entries, 'all')
    accounts.append(account)
  return render_template('generalLedger.html',
    title = 'General Ledger',
    accounts=accounts)

@app.route('/Ledger/<accountName>/<groupby>')
def ledger(accountName, groupby):
  if groupby == "All":
    ledger_entries = models.LedgerEntries.query.\
      filter_by(account=accountName).\
      order_by(models.LedgerEntries.date.desc()).\
      order_by(models.LedgerEntries.entryType.desc()).all()
    account = ledgers.foot_account(accountName, ledger_entries, 'all')
  elif groupby == "Daily":
    debit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(entryType='debit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date)).all()
    credit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(entryType='credit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.date_part('day', models.LedgerEntries.date)).all()
    ledger_entries = {}
    for entry in debit_ledger_entries:
      day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
      if not day in ledger_entries:
        ledger_entries[day] = {}
      ledger_entries[day]['debit'] = int(entry[3])
    for entry in credit_ledger_entries:
      day = datetime.date(int(entry[0]), int(entry[1]), int(entry[2]))
      if not day in ledger_entries:
        ledger_entries[day] = {}
      ledger_entries[day]['credit'] = int(entry[3])
    ledger_entries = OrderedDict(sorted(ledger_entries.items()))
    account = ledgers.foot_account(accountName, ledger_entries, 'summary')
  elif groupby == "Monthly":
    debit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(entryType='debit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date)).all()
    credit_ledger_entries = db.session.query(func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date), func.sum(models.LedgerEntries.amount)).\
      filter_by(account=accountName).\
      filter_by(entryType='credit').\
      group_by( func.date_part('year', models.LedgerEntries.date), func.date_part('month', models.LedgerEntries.date)).all()
    ledger_entries = {}
    for entry in debit_ledger_entries:
      month = datetime.date(int(entry[0]), int(entry[1]), 1)
      if not month in ledger_entries:
        ledger_entries[month] = {}
      ledger_entries[month]['debit'] = int(entry[2])
    for entry in credit_ledger_entries:
      month = datetime.date(int(entry[0]), int(entry[1]), 1)
      if not month in ledger_entries:
        ledger_entries[month] = {}
      ledger_entries[month]['credit'] = int(entry[2])
    ledger_entries = OrderedDict(sorted(ledger_entries.items()))
    account = ledgers.foot_account(accountName, ledger_entries, 'summary')

  return render_template('ledger.html',
    title = 'Ledger',
    account=account,
    ledger_entries=ledger_entries,
    groupby = groupby)
