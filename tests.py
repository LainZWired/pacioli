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
#!flask/bin/python

import os
import fnmatch
import unittest
import uuid
import pacioli

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


class TestCase(unittest.TestCase):
    def setUp(self):
        pacioli.app.config['TESTING'] = True
        pacioli.app.config['WTF_CSRF_ENABLED'] = False
        pacioli.app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://pacioli@localhost/pacioli-test"
        self.app = pacioli.app.test_client()
        pacioli.db.create_all()
        rows = pacioli.db.session.query(pacioli.models.Prices).count()
        if rows == 0:
            pacioli.prices.import_data('pacioli-test')
        print("Setup complete.")

    def tearDown(self):
        pacioli.models.LedgerEntries.query.delete()
        pacioli.db.session.commit()
        pacioli.models.JournalEntries.query.delete()
        pacioli.db.session.commit()
        pacioli.models.MemorandaTransactions.query.delete()
        pacioli.db.session.commit()
        pacioli.models.Memoranda.query.delete()
        pacioli.db.session.commit()
        pacioli.db.session.remove()
        print("Tear down complete.")
    
    def test_empty_uploads(self):
        rv = self.app.get('/Upload')
        page = rv.data.decode("utf-8")
        assert "No files have been uploaded." in page
        
    def test_empty_memoranda(self):
        rv = self.app.get('/Memoranda')
        page = rv.data.decode("utf-8")
        assert "No memoranda have been recorded." in page
        
    def test_empty_memoranda_transactions(self):
        rv = self.app.get('/Memoranda/Transactions')
        page = rv.data.decode("utf-8")
        assert "No memorandum transactions have been recorded." in page
        
    def test_empty_general_journal(self):
        rv = self.app.get('/GeneralJournal')
        page = rv.data.decode("utf-8")
        assert "No journal entries have been recorded." in page
        
    def test_empty_general_ledger(self):
        rv = self.app.get('/GeneralLedger')
        page = rv.data.decode("utf-8")
        assert "No ledger entries have been recorded." in page

    # Too hard, saving this for later
    # def test_upload(self):
    #     response = app_client.post('/Upload', buffered=True,
    #       content_type='multipart/form-data',
    #       data={'file': (io.ByteIO('hello there'), 'hello.txt')})
    #     assert res.status_code == 200
    #     assert 'file saved' in res.data
    
    def test_process_csv(self):
        searchdir = os.path.join(APP_ROOT,'pacioli/data_wallets/')
        matches = []
        for root, dirnames, filenames in os.walk('%s' % searchdir):
            for filename in fnmatch.filter(filenames, '*.csv'):
                matches.append(os.path.join(root,filename))
        for csvfile in matches:
            memoranda_id = str(uuid.uuid4())
            fileName = csvfile.split("/")
            fileName = fileName[-1]
            fileType = fileName.rsplit('.', 1)[1]
            fileSize = os.path.getsize(csvfile)
            with open(csvfile, 'rt') as csvfile:
                fileText = csvfile.read()
                pacioli.memoranda.process_memoranda(fileName, fileType, fileSize, fileText)
        rv = self.app.get('/Upload')
        page = rv.data.decode("utf-8")
        assert '<a href="/Memoranda/MultiBit' in page
        assert '<a href="/Memoranda/Coinbase' in page
        assert '<a href="/Memoranda/Bitcoin' in page
        assert '<a href="/Memoranda/Electrum' in page
        
        rv = self.app.get('/Memoranda/Transactions')
        page = rv.data.decode("utf-8")
        assert '0000000000000000000000000000000000000000000000000000000000000000-000' in page
        assert '1HR5hGL912oTAEWVn4gyY2jjDw259c4XxF' in page
        assert '2013-01-01T01:01:01' in page
        
        rv = self.app.get('/GeneralJournal')
        page = rv.data.decode("utf-8")
        assert '<a href="/Ledger/Expense/All">' in page
        assert '01-01-2013 01:01' in page
        assert '50.0' in page
        
        rv = self.app.get('/GeneralLedger')
        page = rv.data.decode("utf-8")
        assert '<a href="/Ledger/Bitcoins/Monthly/01-2013">' in page
        assert '200.0' in page
        assert '<a href="/Ledger/Expense/All">' in page
        
        rv = self.app.get('/Ledger/Bitcoins/Monthly/01-2013')
        page = rv.data.decode("utf-8")
        assert '<a href="/Ledger/Bitcoins/Daily">' in page
        assert '200.0' in page
        assert '<a href="/GeneralJournal/' in page
        

if __name__ == '__main__':
    unittest.main()
