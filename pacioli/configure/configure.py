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

configure_blueprint = Blueprint('configure', __name__,
template_folder='templates')

@configure_blueprint.route('/')
def index():
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts')
def chart_of_accounts():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    returnrender_template("chart_of_accounts.html",
        subaccounts=subaccounts,
        classificationform=classificationform,
        accountform=accountform,
        subaccountform=subaccountform)

@configure_blueprint.route('/ChartOfAccounts/AddClassification', methods=['POST','GET'])
def add_classification():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['classification']
        parent = form['classificationparent']
        parent = models.Elements.query.filter_by(id=parent).one()
        parent = parent.name
        classification = models.Classifications(name=name, parent=parent)
        db.session.add(classification)
        db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts/DeleteClassification/<classification>')
def delete_classification(classification):
    classification = models.Classifications \
        .query \
        .filter_by(name=classification) \
        .first()
    db.session.delete(classification)
    db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts/AddAccount', methods=['POST','GET'])
def add_account():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['account']
        parent = form['accountparent']
        parent = models.Classifications \
            .query \
            .filter_by(id=parent) \
            .one()
        parent = parent.name
        account = models.Accounts(name=name, parent=parent)
        db.session.add(account)
        db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts/DeleteAccount/<account>')
def delete_account(account):
    account = models.Accounts.query.filter_by(name=account).first()
    db.session.delete(account)
    db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts/AddSubAccount', methods=['POST','GET'])
def add_subaccount():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        name = form['subaccount']
        parent = form['subaccountparent']
        parent = models.Accounts.query.filter_by(id=parent).one()
        parent = parent.name
        subaccount = models.Subaccounts(name=name, parent=parent)
        db.session.add(subaccount)
        db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))

@configure_blueprint.route('/ChartOfAccounts/DeleteSubAccount/<subaccount>')
def delete_subaccount(subaccount):
    subaccount = models.Accounts.query.filter_by(name=subaccount).first()
    db.session.delete(subaccount)
    db.session.commit()
    return redirect(url_for('configure.chart_of_accounts'))
