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


from flask import render_template, request, redirect, url_for, Blueprint
from flask_wtf import Form
from pacioli import app, db, forms, models

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
    return render_template("chart_of_accounts.html",
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
