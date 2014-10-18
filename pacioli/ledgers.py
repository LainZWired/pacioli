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

def foot_account(accountName, entries):
  account = {}
  account['accountName'] = accountName
  account['totalDebit'] = 0
  account['totalCredit'] = 0
  account['debitBalance'] = 0
  account['creditBalance'] = 0
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
