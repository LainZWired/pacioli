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

import datetime
from collections import OrderedDict
from sqlalchemy.sql import func
from pacioli import db, models

def query_entries(accountName, groupby):
  if groupby == "All":
    ledger_entries = models.LedgerEntries.query.\
      filter_by(account=accountName).\
      order_by(models.LedgerEntries.date.desc()).\
      order_by(models.LedgerEntries.entryType.desc()).all()
    account = foot_account(accountName, ledger_entries, 'All')
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
    account = foot_account(accountName, ledger_entries, 'Summary')
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
    account = foot_account(accountName, ledger_entries, 'Summary')
  return [account, ledger_entries]

def foot_account(accountName, entries, interval):
  account = {}
  account['accountName'] = accountName
  account['totalDebit'] = 0
  account['totalCredit'] = 0
  account['debitBalance'] = 0
  account['creditBalance'] = 0
  if interval == 'All':
    for entry in entries:
      if entry.entryType == 'debit' and entry.account == account['accountName']:
        account['totalDebit'] += entry.amount
      elif entry.entryType == 'credit' and entry.account == account['accountName']:
        account['totalCredit'] += entry.amount
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
  elif interval == 'Summary':
    for entry in entries:
      if 'debit' in entries[entry]:
        account['totalDebit'] += entries[entry]['debit']
      if 'credit' in entries[entry]:
        account['totalCredit'] += entries[entry]['credit']
    if account['totalDebit'] > account['totalCredit']:
      account['debitBalance'] = account['totalDebit'] - account['totalCredit']
    elif account['totalDebit'] < account['totalCredit']:
      account['creditBalance'] = account['totalCredit'] - account['totalDebit']
    return account
