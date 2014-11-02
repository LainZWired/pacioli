import pacioli

pacioli.app.config['TESTING'] = True
pacioli.app.config['WTF_CSRF_ENABLED'] = False
pacioli.app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://pacioli@localhost/pacioli-test"
pacioli.db.drop_all()
pacioli.db.create_all()
pacioli.prices.import_summary('pacioli-test')
asset_entry =  pacioli.models.Classifications(name = 'Asset')
pacioli.db.session.add(asset_entry)
liability_entry =  pacioli.models.Classifications(name = 'Liability')
pacioli.db.session.add(liability_entry)
equity_entry =  pacioli.models.Classifications(name = 'Equity')
pacioli.db.session.add(equity_entry)
revenue_entry =  pacioli.models.Classifications(name = 'Revenue')
pacioli.db.session.add(revenue_entry)
expense_entry =  pacioli.models.Classifications(name = 'Expense')
pacioli.db.session.add(expense_entry)
pacioli.db.session.commit()

asset_entry =  pacioli.models.Accounts(name = 'Asset', parent = 'Asset')
pacioli.db.session.add(asset_entry)
bitcoins_entry =  pacioli.models.Accounts(name = 'Bitcoins', parent = 'Asset')
pacioli.db.session.add(bitcoins_entry)
liability_entry =  pacioli.models.Accounts(name = 'Liability', parent = 'Liability')
pacioli.db.session.add(liability_entry)
equity_entry =  pacioli.models.Accounts(name = 'Equity', parent = 'Equity')
pacioli.db.session.add(equity_entry)
revenue_entry =  pacioli.models.Accounts(name = 'Revenue', parent = 'Revenue')
pacioli.db.session.add(revenue_entry)
expense_entry =  pacioli.models.Accounts(name = 'Expense', parent = 'Expense')
pacioli.db.session.add(expense_entry)
pacioli.db.session.commit()
