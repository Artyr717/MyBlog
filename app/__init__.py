import pytz
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
moscow_tz = pytz.timezone('Europe/Moscow')


@app.template_filter('nl2br')
def nl2br_filter(s):
    return Markup(s.replace("\n", "<br>"))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


from app import routes, models, errors
