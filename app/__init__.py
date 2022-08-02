from genericpath import isfile
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from .secret import SECRET_KEY


db = SQLAlchemy()
DB_NAME = 'app.db'


def start_app():
    app = Flask(__name__)
    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'


    csrf = CSRFProtect(app)

    db.init_app(app)

    from .auth import auth
    from .views import views
    from .models import Staff, Client, Year, Month, PaymentData

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_staff(id):
        return Staff.query.get(int(id))

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    return app


def create_database(app):
    if isfile('app/'+DB_NAME):
        print('--- database already created!')
        return
    db.create_all(app=app)
    print('### database successfully created!')