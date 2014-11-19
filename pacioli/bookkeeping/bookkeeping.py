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

bookkeeping_blueprint = Blueprint('bookkeeping', __name__,
template_folder='templates')

@bookkeeping_blueprint.route('/')
def index():
    return redirect(url_for('bookkeeping.upload_csv'))

@bookkeeping_blueprint.route('/Memoranda/Upload', methods=['POST','GET'])
def upload_csv():
    filenames = ''
    if request.method == 'POST':
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            process_filestorage(file)
        return redirect(url_for('bookkeeping.upload_csv'))
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    return render_template('upload.html',
        memos=memos)

@bookkeeping_blueprint.route('/Memoranda/ExchangeRates')
def exchange_rates():
    return render_template('exchange_rates.html')

@bookkeeping_blueprint.route('/Memoranda/DownloadRates')
def download_rates():
    rates.download_rates()
    return redirect(url_for('boookkeeping.exchange_rates'))
  
@bookkeeping_blueprint.route('/Memoranda/ExchangeRates/Summarize')
def summarize_rates():
    rates.summarize_rates("pacioli")
    return redirect(url_for('boookkeeping.exchange_rates'))
  
@bookkeeping_blueprint.route('/Memoranda/ExchangeRates/Import')
def import_rates():
    rates.import_rates("pacioli")
    return redirect(url_for('boookkeeping.exchange_rates'))

@bookkeeping_blueprint.route('/Memoranda/ExchangeRates/CalculateGains/<method>')
def calc_gains(method):
    valuations.calculate_bitcoin_gains(method)
    return redirect(url_for('boookkeeping.exchange_rates'))
    

@bookkeeping_blueprint.route('/Memoranda/Memos', methods=['POST','GET'])
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

    return render_template('memos.html',
        memos=memos)

@bookkeeping_blueprint.route('/Memoranda/Memos/Delete/<filename>')
def delete_memoranda(filename):
    memo = models.Memoranda \
        .query \
        .filter_by(filename=filename) \
        .first()
    db.session.delete(memo)
    db.session.commit()
    return url_for('boookkeeping.upload_csv'))

@bookkeeping_blueprint.route('/Memoranda/Memos/<filename>')
def memo_file(filename):
    memo = models.Memoranda \
        .query \
        .filter_by(filename=filename) \
        .first()
    filetext = memo.filetext
    document = io.StringIO(filetext)
    reader = csv.reader(document)
    rows = [pair for pair in reader]
    return render_template('memo_file.html',
        rows=rows,
        filename=filename)
  
@bookkeeping_blueprint.route('/Memoranda/Memos/Transactions')
def transactions():
    transactions = models.MemorandaTransactions.query.all()
    for transaction in transactions:
        transaction.details = ast.literal_eval(transaction.details)
        journal_entry = models.JournalEntries.query.filter_by(memoranda_transactions_id=transaction.id).first()
        transaction.journal_entry_id = journal_entry.id
    return render_template('memo_transactions.html',
        transactions=transactions)


@bookkeeping_blueprint.route('/Memoranda/Memos/<filename>/Transactions')
def memo_transactions(filename):
    memo = models.Memoranda \
        .query \
        .filter_by(filename=filename) \
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
    return render_template('memo_transactions.html',
        transactions=transactions,
        filename=filename)

@bookkeeping_blueprint.route('/GeneralJournal/<currency>')
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
    return render_template('general_journal.html',
        journal_entries=journal_entries,
        currency=currency)

@bookkeeping_blueprint.route('/JournalEntry/<journal_entry_id>')
def journal_entry(journal_entry_id):
    journal_entry = models.JournalEntries \
        .query \
        .filter_by(id=journal_entry_id) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .order_by(models.LedgerEntries.debit.desc()) \
        .one()
    try:
        transaction = models.MemorandaTransactions \
            .query \
            .filter_by(id=journal_entry.memoranda_transactions_id) \
            .first()
        memo = models.Memoranda \
            .query \
            .filter_by(id=transaction.memoranda_id) \
            .first()
        transaction.details = ast.literal_eval(transaction.details)
    except:
        transaction = None
        memo = None

    return render_template('journal_entry.html',
        journal_entry=journal_entry,
        transaction=transaction,
        memo=memo,
        journal_entry_id=journal_entry_id)

@bookkeeping_blueprint.route('/JournalEntry/Delete/<journal_entry_id>')
def delete_journal_entry(journal_entry_id):
    journal_entry = models.JournalEntries \
        .query \
        .filter_by(id=journal_entry_id) \
        .first()
    db.session.delete(journal_entry)
    db.session.commit()
    return redirect(url_for('boookkeeping.general_journal', currency='Satoshis'))

@bookkeeping_blueprint.route('/JournalEntry/New', methods=['POST','GET'])
def new_journal_entry():
    
    je_form = forms.JournalEntry()
    
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        debit_subaccount = models.Subaccounts.query.filter_by(id=form['debit_ledger']).one()
        credit_subaccount = models.Subaccounts.query.filter_by(id=form['credit_ledger']).one()
        debit_subaccount = debit_subaccount.name
        credit_subaccount = credit_subaccount.name
        date = form['date']
        amount = form['amount']
        currency = form['currency']
        
        journal_entry_id = str(uuid.uuid4())
        debit_ledger_entry_id = str(uuid.uuid4())
        credit_ledger_entry_id = str(uuid.uuid4())
        
        journal_entry = models.JournalEntries(
            id = journal_entry_id)
        db.session.add(journal_entry)
        db.session.commit()
        
        debit_ledger_entry = models.LedgerEntries(
            id = debit_ledger_entry_id,
            date = date,
            debit = amount,
            credit = 0, 
            ledger = debit_subaccount, 
            currency = currency, 
            journal_entry_id = journal_entry_id)
            
        db.session.add(debit_ledger_entry)
        
        credit_ledger_entry = models.LedgerEntries(
            id = credit_ledger_entry_id,
            date = date, 
            debit = 0, 
            credit = amount, 
            ledger = credit_subaccount, 
            currency = currency, 
            journal_entry_id = journal_entry_id)
            
        db.session.add(credit_ledger_entry)
        db.session.commit()
        
        
    return render_template('journal_entry_new.html',
        form=je_form)

@bookkeeping_blueprint.route('/GeneralJournal/<journal_entry_id>/<currency>/Edit', methods=['POST','GET'], defaults={'ledger_entry_id': None})
@bookkeeping_blueprint.route('/GeneralJournal/<journal_entry_id>/<currency>/Edit/<ledger_entry_id>', methods=['POST','GET'])
def edit_journal_entry(journal_entry_id, currency, ledger_entry_id):
    
    if request.method == 'POST':
        if ledger_entry_id:
            form = request.form.copy().to_dict()
            ledger_entry = models.LedgerEntries.query.filter_by(id=ledger_entry_id).one()
            debit_subaccount = models.Subaccounts.query.filter_by(id=form['ledger']).one()
            ledger_entry.date = form['date']
            ledger_entry.debit = form['debit']
            ledger_entry.credit = form['credit']
            ledger_entry.ledger = subaccount.name
            db.session.commit()
        return redirect(url_for('boookkeeping.edit_journal_entry', journal_entry_id=journal_entry_id, currency=currency))
    
    journal_entry = models.JournalEntries \
        .query \
        .filter_by(id=journal_entry_id) \
        .join(models.LedgerEntries) \
        .order_by(models.LedgerEntries.date.desc()) \
        .order_by(models.LedgerEntries.debit.desc()) \
        .one()
            
    for ledger_entry in journal_entry.ledgerentries:
        if ledger_entry.currency == currency:
            ledger_entry.form = forms.EditLedgerEntry()
            ledger_entry.form.date.id = ledger_entry.id
            ledger_entry.form.date.data = ledger_entry.date
            ledger_entry.form.debit.data = ledger_entry.debit
            ledger_entry.form.credit.data = ledger_entry.credit
            ledger_entry.form.ledger.data = ledger_entry.subaccount

    try:
        transaction = models.MemorandaTransactions \
            .query \
            .filter_by(id=journal_entry.memoranda_transactions_id) \
            .first()
        memo = models.Memoranda \
            .query \
            .filter_by(id=transaction.memoranda_id) \
            .first()
        transaction.details = ast.literal_eval(transaction.details)
    except:
        transaction = None
        memo = None
    
    return render_template('journal_entry_edit.html',
        journal_entry_id=journal_entry_id,
        currency = currency, 
        journal_entry=journal_entry,
        transaction=transaction,
        memo=memo)

@bookkeeping_blueprint.route('/<ledger_name>/<currency>/<groupby>',
    defaults={'period_beg': None, 'period_end': None})
@bookkeeping_blueprint.route('/<ledger_name>/<currency>/<groupby>/<period_beg>/<period_end>')
def ledger(ledger_name, currency, groupby, period_beg, period_end):
    if ledger_name == 'GeneralLedger':
        subaccounts = models.Subaccounts.query.all()
    else:
        subaccounts = [models.Subaccounts \
            .query.filter_by(name=ledger_name).one()]
    for subaccount in subaccounts:
        subaccount = ledgers.get_ledger(subaccount, currency, groupby, period_beg, period_end)
    
    return render_template('ledger.html',
        ledger_name = ledger_name,
        currency = currency,
        groupby = groupby,
        period_beg=period_beg,
        period_end=period_end,
        subaccounts = subaccounts)

@bookkeeping_blueprint.route('/TrialBalance/<currency>',
    defaults={'groupby':None, 'period':'Current'})
@bookkeeping_blueprint.route('/TrialBalance/<currency>/<groupby>/<period>')
def trial_balance(currency, groupby, period):
    if groupby == None:
        period = datetime.now()
        lastday = calendar.monthrange(period.year, period.month)[1]
        year = period.year
        month = period.month        
        period_beg = datetime(period.year, period.month, 1, 0, 0, 0, 0).strftime('%Y-%m-%d')
        period_end = datetime(period.year, period.month, lastday, 23, 59, 59, 999999).strftime('%Y-%m-%d')
        return redirect(
            url_for('trial_balance',
            currency='Satoshis',
            groupby='Monthly',
            period='Current'))
            
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
        period = period.strftime("%Y-%m-%d") 

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
            
        period_beg = period - timedelta(days = period.weekday())
        period_end = period_beg + timedelta(days = 6)
        period_beg = datetime(period_beg.year, period_beg.month, period_beg.day, 0, 0, 0, 0)
        period_end = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, 999999)
        periods = sorted([period.strftime("%Y-%W") for period in periods])
        period = period.strftime("%Y-%W") 

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
        periods = sorted([period.strftime("%Y-%m") for period in periods])
        period = period.strftime("%Y-%m")
        
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
        periods = sorted([period.strftime("%Y") for period in periods])
        period = period.strftime("%Y")
    
    subaccounts = db.session \
        .query( \
            models.LedgerEntries.ledger, \
            func.sum(models.LedgerEntries.debit), \
            func.sum(models.LedgerEntries.credit)) \
        .filter(models.LedgerEntries.currency==currency) \
        .filter( models.LedgerEntries.date.between(period_beg, period_end)) \
        .group_by(models.LedgerEntries.ledger) \
        .all()
    totalDebits = 0
    totalCredits = 0
    for subaccount in subaccounts:
            totalDebits += subaccount[1]
            totalCredits += subaccount[2]
    
    return render_template('trial_balance.html',
        groupby=groupby,
        currency=currency,
        periods=periods,
        period=period,
        period_beg=period_beg,
        period_end=period_end,
        totalDebits=totalDebits,
        totalCredits=totalCredits,
        subaccounts=subaccounts)
