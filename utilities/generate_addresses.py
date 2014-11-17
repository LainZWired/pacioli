from pacioli import app
from bitcoinrpc.authproxy import AuthServiceProxy
import csv

access = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (app.config['RPCUSERNAME'], app.config['RPCPASSWORD']))

number = 50
csvfile = open('addresses.csv','a')
writer = csv.writer(csvfile)

while number != 0:
    try:
        newaddress = access.getnewaddress()
        writer.writerow([newaddress])
        print(number)
        number -= 1
    except:
        pass

csvfile.close()
