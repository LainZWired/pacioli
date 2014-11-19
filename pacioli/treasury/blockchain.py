# Experiments going on here
from pacioli import app
from bitcoinrpc.authproxy import AuthServiceProxy

access = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (app.config['RPCUSERNAME'], app.config['RPCPASSWORD']))

def reconcile_transaction(txid, amount, type):
    raw_transaction = access.getrawtransaction(txid, 1)
    vector_out = raw_transaction['vout']
    for utxo in vector_out:
        index = utxo['n']
        utxo_detail = access.gettxout(txid, index)
        if utxo_detail == "None":
            unspent = False
        elif 'bestblock' in utxo_detail:
            unspent = True
        print(utxo_detail)
