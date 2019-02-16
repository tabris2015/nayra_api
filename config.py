import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nayra2019'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['eduardo.laruta@gmail.com']

    # for file uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'files')
    AUDIOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'audios')
    PROGRAMS_FOLDER = os.path.join(UPLOAD_FOLDER, 'programs')
    GRAMMARS_FOLDER = os.path.join(basedir, 'gram')
    GRAMMAR_TEMPLATE = "grammar.txt"

    # cors
    CORS_HEADERS = 'Content-Type'
    
