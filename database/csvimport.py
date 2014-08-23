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

import os
import fnmatch
import sys
import csv
import json
import uuid
import api

def multibit_import(csvfile):
    with open(csvfile, 'rt') as csvfile:
        filename = csvfile.name
        reader = csv.reader(csvfile)
        # Numbering each row
        reader = enumerate(reader)
        # Create a list of lists:
        rows = [pair for pair in reader]
        # Find the first longest list:
        header = max(rows,key=lambda tup:len(tup[1]))
        # Create a list that contains all the rows under the header:
        tx_list = []
        for row in rows:
            is_transaction = row[0] > header[0]
            if is_transaction:
                transaction = row[1]
                tx_list.append(transaction)

        for tx in tx_list:
            record = zip(header[1], tx)
            record = dict(record)
            journal_entry = {}
            journal_entry['entry_space'] = 'GeneralJournal'
            journal_entry['unique'] = str(uuid.uuid4())
            journal_entry['Date'] = record['Date']
            journal_entry['Debits'] = []
            journal_entry['Credits'] = []

            debit_ledger_entry = {}
            debit_ledger_entry['entry_space'] = 'GeneralLedger'
            debit_ledger_entry['unique'] = str(uuid.uuid4())
            journal_entry['Debits'].append(debit_ledger_entry['unique'])
            debit_ledger_entry['Date'] = record['Date']
            debit_ledger_entry['Type'] = "Debit"
            debit_ledger_entry['Amount'] = int(abs(float(record['Amount']))*100000000)
            debit_ledger_entry['Unit'] = "satoshis"
            debit_ledger_entry['gjUUID'] = "Debit"

            credit_ledger_entry = {}
            credit_ledger_entry['entry_space'] = 'GeneralLedger'
            credit_ledger_entry['unique'] = str(uuid.uuid4())
            journal_entry['Credits'].append(debit_ledger_entry['unique'])
            print(journal_entry['Credits'])
            credit_ledger_entry['Date'] = record['Date']
            credit_ledger_entry['Type'] = "Credit"
            credit_ledger_entry['Amount'] = int(abs(float(record['Amount']))*100000000)
            credit_ledger_entry['Unit'] = "satoshis"
            credit_ledger_entry['gjUUID'] = "Credit"

            if int(abs(float(record['Amount']))*100000000) > 0:
              debit_ledger_entry['Account'] = "Bitcoins"
              credit_ledger_entry['Account'] = "Revenue"
            elif int(abs(float(record['Amount']))*100000000) < 0:
              debit_ledger_entry['Account'] = "Expense"
              credit_ledger_entry['Account'] = "Bitcoins"
            journal_entry['Debits']= set(journal_entry['Debits'])
            journal_entry['Credits']= set(journal_entry['Credits'])
            print(api.add_record(journal_entry))
            print(api.add_record(debit_ledger_entry))
            print(api.add_record(credit_ledger_entry))


def main():
    if len(sys.argv) <2:
        sys.exit('Missing argument: specify the folder of CSV files you want to convert.')
    searchdir = sys.argv[1]
    matches = []
    for root, dirnames, filenames in os.walk('%s' % searchdir):
        for filename in fnmatch.filter(filenames, '*.csv'):
            matches.append(os.path.join(root,filename))
    for csvfile in matches:
        result = multibit_import(csvfile)
        if not result:
            sys.exit(1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
