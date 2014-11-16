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

from datetime import datetime, date, timedelta
from collections import OrderedDict
from sqlalchemy.sql import func
from pacioli import db, models
import pacioli.accounting.rates as rates
from dateutil import parser
from operator import itemgetter
import calendar
from isoweek import Week

def get_ledger(subaccount, currency, groupby, period_beg=None, period_end=None):
    name = subaccount.name

    if period_beg and period_end:
        period_beg = datetime.strptime(period_beg, "%Y-%m-%d")
        period_end = datetime.strptime(period_end, "%Y-%m-%d")
        period_beg = datetime(period_beg.year, period_beg.month, period_beg.day, 0, 0, 0, 0)
        period_end = datetime(period_end.year, period_end.month, period_end.day, 23, 59, 59, 999999)

    if groupby == "All":
        ledgers_query = db.session \
            .query( \
                models.LedgerEntries.ledger, \
                models.LedgerEntries.debit, \
                models.LedgerEntries.credit, \
                models.LedgerEntries.date, \
                models.LedgerEntries.journal_entry_id) \
            .filter_by(currency=currency) \
            .filter_by(ledger=name) \
            .all()

    elif groupby == "Daily":
        ledgers_query = db.session \
            .query( \
                models.LedgerEntries.ledger, \
                func.sum(models.LedgerEntries.debit), \
                func.sum(models.LedgerEntries.credit), \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .filter_by(currency=currency) \
            .filter_by(ledger=name) \
            .group_by( \
                models.LedgerEntries.ledger, \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date), \
                func.date_part('day', models.LedgerEntries.date)) \
            .all()

    elif groupby == "Weekly":
        ledgers_query = db.session \
            .query( \
                models.LedgerEntries.ledger, \
                func.sum(models.LedgerEntries.debit), \
                func.sum(models.LedgerEntries.credit), \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('week', models.LedgerEntries.date)) \
            .filter_by(currency=currency) \
            .filter_by(ledger=name) \
            .group_by( \
                models.LedgerEntries.ledger, \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('week', models.LedgerEntries.date)) \
            .all()

    elif groupby == "Monthly":
        ledgers_query = db.session \
            .query( \
                models.LedgerEntries.ledger, \
                func.sum(models.LedgerEntries.debit), \
                func.sum(models.LedgerEntries.credit), \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .filter_by(currency=currency) \
            .filter_by(ledger=name) \
            .group_by( \
                models.LedgerEntries.ledger, \
                func.date_part('year', models.LedgerEntries.date), \
                func.date_part('month', models.LedgerEntries.date)) \
            .all()
    
    subaccount.ledgers = []
    subaccount.totalDebits = 0
    subaccount.totalCredits = 0
    subaccount.debitBalance = 0
    subaccount.creditBalance = 0

    for result in ledgers_query:
        if result[0] == subaccount.name:
            if groupby == "All":
                ledger = result
            elif groupby == "Daily":
                ledger = [result[0], result[1], result[2], datetime(int(result[3]), int(result[4]), int(result[5]), 23, 59, 59, 999999)]
            elif groupby == "Weekly":
                ledger = [result[0], result[1], result[2],  datetime.combine(Week(int(result[3]), int(result[4])).monday(),datetime.min.time())]
            elif groupby == "Monthly":
                lastday = calendar.monthrange(int(result[3]), int(result[4]))[1]
                ledger = [result[0], result[1], result[2], datetime(int(result[3]), int(result[4]), lastday, 23, 59, 59, 999999)]
            if period_beg and period_end:
                if period_beg <= ledger[3] <= period_end:
                    subaccount.ledgers.append(ledger)
            else:
                subaccount.ledgers.append(ledger)
            subaccount.totalDebits += ledger[1]
            subaccount.totalCredits += ledger[2]
    subaccount.ledgers = sorted(subaccount.ledgers, key=itemgetter(3))
    if subaccount.totalDebits > subaccount.totalCredits:
        subaccount.debitBalance = subaccount.totalDebits - subaccount.totalCredits
    elif subaccount.totalDebits < subaccount.totalCredits:
        subaccount.creditBalance = subaccount.totalCredits - subaccount.totalDebits
    return subaccount
