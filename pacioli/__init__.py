from flask import Flask
from flask.ext.babel import Babel
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
babel = Babel(app)
db = SQLAlchemy(app)

@app.context_processor
def utility_processor():
    def format_satoshis(amount):
        return u'{:,}'.format(amount)
    return dict(format_satoshis=format_satoshis)

from pacioli import views, models, forms
