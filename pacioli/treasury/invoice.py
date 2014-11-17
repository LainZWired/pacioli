import bitcoin.rpc
import gnupg
import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "you@gmail.com"
SMTP_PASSWORD = "password"
EMAIL_FROM = SMTP_USERNAME
EMAIL_TO = 'vendor@email.org'
GNUPGHOME= '/Users/YOURUSERNAME/.gnupg'

gpg = gnupg.GPG(gnupghome=GNUPGHOME)
proxy = bitcoin.rpc.Proxy()

newaddress = proxy.getnewaddress()

public_keys = gpg.list_keys()

for public_key in public_keys:
    uids = public_key['uids']
    if any(EMAIL_TO in s for s in uids):
        recipient_fingerprint = public_key['fingerprint']
        print(recipient_fingerprint)

data = "Pay to " + str(newaddress)

encrypted_ascii_data = gpg.encrypt(data, recipient_fingerprint)


msg = MIMEText(str(encrypted_ascii_data))
msg['Subject'] = 'wut'
msg['To'] = EMAIL_TO
msg['From'] = EMAIL_FROM
mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
mail.starttls()
mail.login(SMTP_USERNAME, SMTP_PASSWORD)
mail.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
mail.quit()
