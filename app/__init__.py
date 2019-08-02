import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS, cross_origin
from flask_restful import Api

from config import Config
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
import os


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
cors = CORS(app, supports_credentials=True)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
api = Api(app, "/api")

# cors
# cors = CORS(app, resources)


from app import routes, models, errors
from app.resources.audio_category import AudioCategoryRes, AudioCategoryListRes
from app.resources.audio import AudioRes, AudioListRes


api.add_resource(AudioCategoryRes, "/audios/categories/<int:ac_id>")
api.add_resource(AudioCategoryListRes, "/audios/categories")
api.add_resource(AudioRes, "/audios/<int:audio_id>")
api.add_resource(AudioListRes, "/audios")


if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='nayra Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/nayra.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('nayra startup')
