import bitcoin.rpc
import gnupg
import uuid
import smtplib
from datetime import datetime
from pacioli import app, models, db
from email.mime.text import MIMEText
from decimal import Decimal

gpg = gnupg.GPG(gnupghome=app.config['GNUPGHOME'])
bitcoind = bitcoin.rpc.Proxy()

def get_contacts():
    
    public_keys = gpg.list_keys()
    return public_keys

def get_fingerprint(email):
    public_keys = gpg.list_keys()
    for public_key in public_keys:
        uids = public_key['uids']
        if any(email in s for s in uids):
            fingerprint = public_key['fingerprint']
            if fingerprint:
                return fingerprint
            else:
                return None

def send_invoice(email_to, amount, customer_order_id):
    invoice_id = str(uuid.uuid4())
    bitcoin_address = bitcoind.getnewaddress()

    public_keys = gpg.list_keys()

    for public_key in public_keys:
        uids = public_key['uids']
        if any(email_to in s for s in uids):
            recipient_fingerprint = public_key['fingerprint']

    data = "address:%s, amount:%s, id:%s" % (bitcoin_address, amount, invoice_id)
    encrypted_ascii_data = gpg.encrypt(data, recipient_fingerprint)

    msg = MIMEText(str(encrypted_ascii_data))
    msg['Subject'] = 'pacioli'
    msg['To'] = email_to
    msg['From'] = app.config['SMTP_USERNAME']
    mail = smtplib.SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT'])
    mail.starttls()
    mail.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
    mail.sendmail(app.config['SMTP_USERNAME'], email_to, msg.as_string())
    mail.quit()
    
    date_sent = datetime.now()
    
    invoice = models.Invoices(
        id = invoice_id,
        sent = date_sent,
        bitcoin_address = str(bitcoin_address),
        customer_order_id = customer_order_id)
    db.session.add(invoice)
    db.session.commit()
    
    return date_sent

def get_cash_receipts():
    cash_receipts = bitcoind.listreceivedbyaddress(0)
    print(cash_receipts)
