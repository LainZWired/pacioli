import bitcoin.rpc
import gnupg
import uuid
import smtplib
from pacioli import app
from email.mime.text import MIMEText

def send_invoice(email_to, amount, customer_order_id):
    gpg = gnupg.GPG(gnupghome=app.config['GNUPGHOME'])
    proxy = bitcoin.rpc.Proxy()
    invoice_id = str(uuid.uuid4())
    bitcoin_address = proxy.getnewaddress()

    public_keys = gpg.list_keys()

    for public_key in public_keys:
        uids = public_key['uids']
        if any(EMAIL_TO in s for s in uids):
            recipient_fingerprint = public_key['fingerprint']
            print(recipient_fingerprint)

    data = """\
    <html>
    <head></head>
      <body>
        <p>
        <a href='bitcoin:%s?amount=%d'>Pay Invoice</a>" % (bitcoin_address, amount)
        </p>
        <p>
        %s
        </p>
      </body>
    </html>
    """ % (bitcoin_address, amount, invoice_id)
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
    
    invoice = models.Invoices(
        id = invoice_id,
        sent = datetime.now(),
        bitcoin_address = bitcoin_address,
        customer_order_id = customer_order_id)
    db.session.add(invoice)
    db.session.commit()
