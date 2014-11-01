from bitcoinrpc.authproxy import AuthServiceProxy
import csv

access = AuthServiceProxy("http://rpcusername:rpcpassword@127.0.0.1:8332")

number = 100

while number != 0:
    try:
        newaddress = access.getnewaddress('account')
        csvfile = open('addresses.csv','a')
        writer = csv.writer(csvfile)
        writer.writerow([newaddress])
        csvfile.close()
        print number
        number -= 1
    except:
        pass
