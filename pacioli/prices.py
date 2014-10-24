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
import fnmatch
import io
from datetime import datetime, date, timezone
import time
import logging
import sys
import csv
import json
import uuid
from pacioli import app, db, models
from sqlalchemy.sql import func, extract
from sqlalchemy import exc


APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def import_data():
    searchdir = os.path.join(APP_ROOT,'price_data/')
    matches = []
    for root, dirnames, filenames in os.walk('%s' % searchdir):
        for filename in fnmatch.filter(filenames, '*.csv'):
            matches.append(os.path.join(root,filename))
    for csvfile in matches:
        print(csvfile)
        result = csv_import(csvfile)
    return True

def csv_import(csvfile):
  with open(csvfile, 'rt') as csvfile:
      reader = csv.reader(csvfile)
      # Numbering each row
      reader = enumerate(reader)
      # Turns the enumerate object into a list
      rows = [pair for pair in reader]
      # Find the first longest list:
      header = max(rows, key=lambda tup:len(tup[1]))
      if header[1] == ["timestamp","vwap"]:
        return _import_price_bitstamp(rows, header)
      else:
        return False
      return False
  
def _import_price_bitstamp(rows, header):
  for row in rows:
    if row[0] > header[0] and len(row[1]) == len(header[1]):
      memoranda = zip(header[1], row[1])
      memoranda = dict(memoranda)
      price_id = str(uuid.uuid4())
      date = datetime.fromtimestamp(int(memoranda['timestamp']))
      currency = "USD"
      if memoranda['vwap']:
          rate = int(abs(float(memoranda['vwap']))*100)
          source = "bitstamp"
          price_entry = models.Prices(id=price_id, source=source, date=date, currency=currency, rate=rate)
          db.session.add(price_entry)
          db.session.commit()
  return True

def getRate(date):
    date = int(date.strftime('%s'))
    closest_price = db.session.query(models.Prices.rate).order_by(func.abs( date -  extract('epoch', models.Prices.date))).first()
    return int(closest_price[0]/100000000000)

# select id, passed_ts - ts_column difference
# from t
# where
#     passed_ts > ts_column and positive_interval
#     or
#     passed_ts < ts_column and not positive_interval
# order by abs(extract(epoch from passed_ts - ts_column))
# limit 1
