import bitcoin.rpc
import gnupg
import uuid
import smtplib
import imaplib
from datetime import datetime
from pacioli import app, models, db
from email.mime.text import MIMEText
from decimal import Decimal

gpg = gnupg.GPG(gnupghome=app.config['GNUPGHOME'])
bitcoind = bitcoin.rpc.Proxy()

def fetch_email():
    mail = imaplib.IMAP4_SSL(app.config['IMAP_SERVER'])
    mail.login(app.config['IMAP_USERNAME'], app.config['IMAP_PASSWORD'])
    mail.list()
    # Out: list of "folders" aka labels in gmail.
    mail.select("inbox") # connect to inbox.
    result, data = mail.search(None, "ALL")
    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string
    latest_email_id = id_list[-1] # get the latest
     
    result, data = mail.fetch(latest_email_id, "(RFC822)") # fetch the email body (RFC822) for the given ID
     
    raw_email = data[0][1] # here's the body, which is raw text of the whole email
    # including headers and alternate payloads
    print(raw_email)

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

def send_invoice(email_to, amount, sales_order_id):
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
    mail = smtplib.SMTP_SSL(app.config['SMTP_SERVER'], app.config['SMTP_PORT'])
    mail.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
    mail.sendmail(app.config['SMTP_USERNAME'], email_to, msg.as_string())
    mail.quit()
    
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
