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
        return redirect(url_for('upload_csv'))
    memos = models.Memoranda \
        .query \
        .order_by(models.Memoranda.date.desc()) \
        .all()
    return render_template('upload.html',
        title = 'Upload',
        memos=memos)
