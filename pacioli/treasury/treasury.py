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
from pacioli.bookkeeping.memoranda import process_filestorage
import pacioli.bookkeeping.ledgers as ledgers
import pacioli.bookkeeping.rates as rates
import pacioli.bookkeeping.valuations as valuations
import pacioli.treasury.treasury_utilities as treasury_utilities
from decimal import Decimal

treasury_blueprint = Blueprint('treasury', __name__,
template_folder='templates')

def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

@treasury_blueprint.route('/')
def index():
    return redirect(url_for('treasury.customers'))

@treasury_blueprint.route('/NewIdentity', methods=['POST','GET'])
def new_identity():
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        identity_id = str(uuid.uuid4())
        first_name = form['first_name']
        last_name = form['last_name']
        irc_nick = form['irc_nick']
        email = form['email']
        fingerprint = treasury_utilities.get_fingerprint(email)
        identity = models.Identities(id=identity_id,
            first_name=first_name, 
            last_name=last_name, 
            irc_nick=irc_nick, 
            email=email,
            fingerprint=fingerprint)
        db.session.add(identity)
        db.session.commit()
    return redirect(redirect_url())

@treasury_blueprint.route('/DeleteIdentity/<identity_id>')
def delete_identity(customer_id):
    identity = models.Identities \
        .query \
        .filter_by(id=identity_id) \
        .first()
    db.session.delete(identity)
    db.session.commit()
    return redirect(redirect_url())
    
@treasury_blueprint.route('/RevenueCycle')
def revenue_cycle():
    return redirect(url_for('treasury.customers'))

@treasury_blueprint.route('/RevenueCycle/Identities')
def customers():
    customers = models.Identities.query.all()
    identity_form = forms.NewIdentity()
    return render_template("revenue_cycle/customers.html",
        identity_form=identity_form,
        customers=customers)

@treasury_blueprint.route('/RevenueCycle/NewSalesOrders')
def new_sales_orders():
    sales_orders = models.SalesOrders.query.all()
    # Create a form for approval of new sales orders
    return render_template("revenue_cycle/new_sales_orders.html",
    sales_orders=sales_orders)

@treasury_blueprint.route('/RevenueCycle/NewSalesOrders/Retrieve')
def retrieve_new_sales_orders():
    new_orders = treasury_utilities.fetch_email()
    return redirect(url_for('treasury.new_sales_orders'))
    
@treasury_blueprint.route('/RevenueCycle/OpenSalesOrders')
def open_sales_orders():
    # Filter for orders that are open
    sales_orders = models.SalesOrders.query.all()
    return render_template("revenue_cycle/open_sales_orders.html",
    sales_orders=sales_orders)

    
@treasury_blueprint.route('/RevenueCycle/AccountsReceivable')
def accounts_receivable():
    outstanding_invoices = models.SalesInvoices.query.all()
    return render_template("revenue_cycle/accounts_receivable.html",
        outstanding_invoices=outstanding_invoices)
    
    # invoice_customer is a short cut for sending an invoice
    # to someone who has not sent you a sales order
    
@treasury_blueprint.route('/RevenueCycle/InvoiceCustomer/<customer_id>', methods=['POST','GET'])
def invoice_customer(customer_id):
    customer = models.Identities \
    .query \
    .filter_by(id=customer_id) \
    .first()
    invoice_form = forms.NewInvoice()
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        amount = form['amount']
        sales_order_id = str(uuid.uuid4())
        now = datetime.now()
        customer_order = models.SalesOrders(id=sales_order_id,
            received_date=now,
            approved_date=now,
            shipped_date=now,
            customer_id=customer.id)
        db.session.add(customer_order)
        db.session.commit()
        date_sent = treasury_utilities.send_invoice(customer.email, amount, sales_order_id)
        
        amount = Decimal(amount)*100000000
        print(amount)
        journal_entry_id = str(uuid.uuid4())
        debit_ledger_entry_id = str(uuid.uuid4())
        credit_ledger_entry_id = str(uuid.uuid4())
        
        journal_entry = models.JournalEntries(
        id = journal_entry_id)
        db.session.add(journal_entry)
        db.session.commit()
        
        debit_ledger_entry = models.LedgerEntries(
        id = debit_ledger_entry_id,
        date = date_sent,
        debit = amount,
        credit = 0, 
        ledger = 'Accounts Receivable', 
        currency = 'Satoshis', 
        journal_entry_id = journal_entry_id)
        
        db.session.add(debit_ledger_entry)
        
        credit_ledger_entry = models.LedgerEntries(
        id = credit_ledger_entry_id,
        date = date_sent, 
        debit = 0, 
        credit = amount, 
        ledger = 'Revenues', 
        currency = 'Satoshis', 
        journal_entry_id = journal_entry_id)
        
        db.session.add(credit_ledger_entry)
        db.session.commit()
        return redirect(url_for('treasury.accounts_receivable'))
    return render_template("revenue_cycle/new_invoice.html",
    invoice_form=invoice_form,
    customer=customer)
            
@treasury_blueprint.route('/RevenueCycle/AccountsReceivable/DeleteInvoice/<invoice_id>')
def delete_invoice(invoice_id):
    invoice = models.SalesInvoices.query.filter_by(id=invoice_id).first()
    db.session.delete(invoice)
    db.session.commit()
    return redirect(url_for('treasury.accounts_receivable'))
    
@treasury_blueprint.route('/RevenueCycle/CashReceipts')
def cash_receipts():
    cash_receipts = treasury_utilities.get_cash_receipts()
    return render_template("revenue_cycle/cash_receipts.html",
        cash_receipts=cash_receipts)

@treasury_blueprint.route('/RevenueCycle/ClosedSalesOrders')
def closed_sales_orders():
    # Filter for orders that are closed
    sales_orders = models.SalesOrders.query.all()
    return render_template("revenue_cycle/closed_sales_orders.html",
    sales_orders=sales_orders)
    
@treasury_blueprint.route('/RevenueCycle/SalesRefunds')
def sales_refunds():
    # Filter for refund requests
    sales_orders = models.SalesOrders.query.all()
    return render_template("revenue_cycle/sales_refunds.html",
    sales_orders=sales_orders)

@treasury_blueprint.route('/ExpenditureCycle')
def expenditure_cycle():
    return redirect(url_for('treasury.vendors'))

@treasury_blueprint.route('/ExpenditureCycle/Vendors')
def vendors():
    vendors = models.Identities.query.all()
    identity_form = forms.NewIdentity()
    return render_template("expenditure_cycle/vendors.html",
        identity_form=identity_form,
        vendors=vendors)

@treasury_blueprint.route('/ExpenditureCycle/NewPurchaseOrder/<vendor_id>')
def new_purchase_order(vendor_id):
    vendor = models.Identities.query.filter_by(id=vendor_id).one()
    purchase_order_id = str(uuid.uuid4())
    purchase_order = models.PurchaseOrders(
        id=purchase_order_id,
        vendor_id=vendor_id)
    db.session.add(purchase_order)
    db.session.commit()
    return redirect(url_for('treasury.new_purchase_order_items', purchase_order_id=purchase_order_id))
    
@treasury_blueprint.route('/ExpenditureCycle/NewPurchaseOrder/Items/<purchase_order_id>', methods=['POST','GET'])
def new_purchase_order_items(purchase_order_id):
    purchase_order = models.PurchaseOrders.query.filter_by(id=purchase_order_id).one()
    purchase_order_item = forms.NewPurchaseOrderItem()
    if request.method == 'POST':
        form = request.form.copy().to_dict()
        order_item_id = str(uuid.uuid4())
        item_id = form['item']
        item = models.Items.query.filter_by(id=item_id).one()
        item = item.name
        unit_price = form['unit_price']
        currency = form['currency']
        quantity_ordered = form['quantity_ordered']
        order_item = models.PurchaseOrderItems(id=order_item_id,
            unit_price=unit_price,
            quantity_ordered=quantity_ordered,
            quantity_received=quantity_ordered,
            currency=currency,
            item=item,
            purchase_order_id=purchase_order_id)
        db.session.add(order_item)
        db.session.commit()
        return redirect(url_for('treasury.new_purchase_order_items', purchase_order_id=purchase_order_id))
    return render_template("expenditure_cycle/new_purchase_order.html",
        purchase_order=purchase_order,
        purchase_order_item=purchase_order_item)

@treasury_blueprint.route('/ExpenditureCycle/NewPurchaseOrder/Send/<purchase_order_id>')
def send_purchase_order(purchase_order_id):
    purchase_order = models.PurchaseOrders.query.filter_by(id=purchase_order_id).one()
    return redirect(url_for('treasury.open_purchase_orders'))

@treasury_blueprint.route('/ExpenditureCycle/OpenPurchaseOrders')
def open_purchase_orders():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    return render_template("expenditure_cycle/open_purchase_orders.html")

@treasury_blueprint.route('/ExpenditureCycle/AccountsPayable')
def accounts_payable():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    return render_template("expenditure_cycle/accounts_payable.html")

@treasury_blueprint.route('/ExpenditureCycle/ClosedPurchaseOrders')
def closed_purchase_orders():
    classificationform = forms.NewClassification()
    accountform = forms.NewAccount()
    subaccountform = forms.NewSubAccount()
    subaccounts = models.Subaccounts.query.all()
    return render_template("expenditure_cycle/closed_purchase_orders.html")
