Pacioli
=======

Pacioli is Bitcoin accounting software implemented with a Python/Flask/PostgreSQL stack.


## Guide to Installing Pacioli

1. Install [PostgreSQL](http://www.postgresql.org/)
2. Create a user called pacioli and a new database ([Instructions](http://killtheyak.com/use-postgresql-with-django-flask/))
3. [Fork the repository](https://help.github.com/articles/fork-a-repo/)
4. Create a virtual environment <code>python3 -m venv venv</code>
5. Activate the virtual environment <code>. venv/bin/activate</code>
5. Install the requirements <code>pip install -r requirements.txt</code>
6. Run <code>python db_create.py</code>
7. Run <code>python run.py</code>
