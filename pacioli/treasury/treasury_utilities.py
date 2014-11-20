import bitcoin.rpc
import gnupg
import uuid
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from decimal import Decimal
from datetime import datetime
from pacioli import app, models, db


gpg = gnupg.GPG(gnupghome=app.config['GNUPGHOME'])
bitcoind = bitcoin.rpc.Proxy()


def send_gpg_email(email_to, data):
    public_keys = gpg.list_keys()
    for public_key in public_keys:
        uids = public_key['uids']
        if any(email_to in s for s in uids):
            recipient_fingerprint = public_key['fingerprint']
    encrypted_ascii_data = gpg.encrypt(data, recipient_fingerprint)
    msg = MIMEText(str(encrypted_ascii_data))
    msg['Subject'] = 'pacioli'
    msg['To'] = email_to
    msg['From'] = app.config['SMTP_USERNAME']
    mail = smtplib.SMTP_SSL(app.config['SMTP_SERVER'], app.config['SMTP_PORT'])
    mail.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
    mail.sendmail(app.config['SMTP_USERNAME'], email_to, msg.as_string())
    mail.quit()
    

def fetch_email():
    mail = imaplib.IMAP4_SSL(app.config['IMAP_SERVER'])
    mail.login(app.config['IMAP_USERNAME'], app.config['IMAP_PASSWORD'])
    mail.list()
    mail.select("inbox") 
    result, data = mail.uid('search', None, "ALL") 
    ids = data[0]
    id_list = ids.split()
    print(id_list)
    latest_email_uid = id_list[-1]
    result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
    raw_email = data[0][1]
    email_message = email.message_from_bytes(raw_email)
    print(email_message.items())

    maintype = email_message.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message.get_payload():
            if part.get_content_maintype() == 'text':
                content= part.get_payload()
    elif maintype == 'text':
        content= email_message.get_payload()
    print(content)
    decrypted_data = gpg.decrypt(content)
    print(decrypted_data)

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

def send_purchase_order(purchase_order):
    return True
                
def send_invoice(email_to, amount, sales_order_id):
    invoice_id = str(uuid.uuid4())
    bitcoin_address = bitcoind.getnewaddress()
    data = "address:%s, amount:%s, id:%s" % (bitcoin_address, amount, invoice_id)
    
    send_gpg_email(email_to, data)
    sent_date = datetime.now()
    
    invoice = models.SalesInvoices(
        id = invoice_id,
        sent_date = sent_date,
        bitcoin_address = str(bitcoin_address),
        sales_order_id = sales_order_id)
    db.session.add(invoice)
    db.session.commit()
    return sent_date

    
def get_cash_receipts():
    cash_receipts = bitcoind.listreceivedbyaddress(0)
    
    return cash_receipts

def reconcile_transaction(txid, amount, type):
    raw_transaction = bitcoind.getrawtransaction(txid, 1)
    vector_out = raw_transaction['vout']
    for utxo in vector_out:
        index = utxo['n']
        utxo_detail = bitcoind.gettxout(txid, index)
        if utxo_detail == "None":
            unspent = False
        elif 'bestblock' in utxo_detail:
            unspent = True
        print(utxo_detail)
