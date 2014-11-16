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

from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy
import calendar
from isoweek import Week
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.config.from_object('config')
babel = Babel(app)
db = SQLAlchemy(app)

@app.context_processor
def utility_processor():
    def format_satoshis(amount):
        return u'{:,}'.format(abs(amount)/100000000)
    def format_usd(amount):
        return u"${:,.2f}".format(abs(amount))
    def format_date(groupby, date):
        if groupby == "All":
            return date.strftime('%Y-%m-%d %X')                
        elif groupby == "Daily":
            return date.strftime('%Y-%m-%d')
        elif groupby == "Weekly":
            return date.strftime("%Y-%W")
        elif groupby == "Monthly":
            return date.strftime('%Y-%m')
        elif groupby == "Annual":
            return date.strftime('%Y')

    def beg(groupby, date):
        if groupby == "Daily":
            return date.strftime('%Y-%m-%d')
        elif groupby == "Weekly":
            date = datetime(date.year, date.month, date.day, 0, 0, 0, 0)
            return date.strftime('%Y-%m-%d')
        elif groupby == "Monthly":
            date = datetime(date.year, date.month, 1, 0, 0, 0, 0)
            return date.strftime('%Y-%m-%d')
        elif groupby == "Annual":
            date = datetime.strptime(date, "%Y")
            date = datetime(date.year, 1, 1, 0, 0, 0, 0)
            return date.strftime('%Y-%m-%d')
            
    def end(groupby, date):
        if groupby == "Daily":
            return date.strftime('%Y-%m-%d')
        elif groupby == "Weekly":
            date = datetime(date.year, date.month, date.day,  23, 59, 59, 999999)
            date = date + timedelta(days = 6)
            return date.strftime('%Y-%m-%d')
        elif groupby == "Monthly":
            lastday = calendar.monthrange(date.year, date.month)[1]
            date = datetime(date.year, date.month, lastday, 23, 59, 59, 999999)
            return date.strftime('%Y-%m-%d')
        elif groupby == "Annual":
            date = datetime.strptime(date, "%Y")
            date = datetime(date.year, 12, 31, 23, 59, 59, 999999)
            return date.strftime('%Y-%m-%d')
            
    return dict(format_usd=format_usd, 
                format_satoshis=format_satoshis,
                format_date=format_date,
                beg=beg,
                end=end)

from pacioli import views, models, forms
