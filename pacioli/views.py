from flask import flash, render_template, request, redirect, url_for, send_from_directory, send_file
from pacioli import app, db, forms, models
import io
import uuid
import os
import datetime
import pacioli.memoranda
import ast

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
def memo_transactions(fileName):
  memo = models.Memoranda.query.filter_by(fileName=fileName).first()
  transactions = models.MemorandaTransactions.query.filter_by(memoranda_id=memo.id).all()
  for transaction in transactions:
    transaction.details = ast.literal_eval(transaction.details)
    journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
    transaction.journal_entry_id = journal_entry.id
  return render_template('memoTransactions.html',
    title = 'Memo',
    transactions=transactions)

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
  entries = models.LedgerEntries.query.order_by(models.LedgerEntries.date.desc()).order_by(models.LedgerEntries.entryType.desc()).all()
  accounts = []
  for accountResult in accountsQuery:
    account = {}
    account['accountName'] = accountResult[0]
    account['totalDebit'] = 0
    account['totalCredit'] = 0
    account['debitBalance'] = ''
    account['creditBalance'] = ''
    for entry in entries:
      if entry.entryType == 'debit' and entry.account == account['accountName']:
        account['totalDebit'] += entry.amount
      elif entry.entryType == 'credit' and entry.account == account['accountName']:
        account['totalCredit'] += entry.amount
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    accounts.append(account)
  return render_template('generalLedger.html',
    title = 'General Ledger',
    accounts=accounts)

@app.route('/Ledger/<accountName>')
def ledger(accountName):
  entries = models.LedgerEntries.query.\
    filter_by(account=accountName).\
    order_by(models.LedgerEntries.date.desc()).\
    order_by(models.LedgerEntries.entryType.desc()).all()
  account = {}
  account['accountName'] = accountName
  account['totalDebit'] = 0
  account['totalCredit'] = 0
  account['debitBalance'] = ''
  account['creditBalance'] = ''
  for entry in entries:
    if entry.entryType == 'debit' and entry.account == account['accountName']:
      account['totalDebit'] += entry.amount
    elif entry.entryType == 'credit' and entry.account == account['accountName']:
      account['totalCredit'] += entry.amount
  if account['totalDebit'] > account['totalCredit']:
    account['debitBalance'] = account['totalDebit'] - account['totalCredit']
  elif account['totalDebit'] < account['totalCredit']:
    account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    
  return render_template('ledger.html',
    title = 'Ledger',
    account=account,
    entries=entries)
