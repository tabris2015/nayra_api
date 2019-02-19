from datetime import datetime
from hashlib import md5
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


# modelo para los audios
class Audio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    content = db.Column(db.String(128), index=True)
    filepath = db.Column(db.String(120), index=True, unique=True)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    category = db.Column(db.String(64), index=True, default="audio")

    def __repr__(self):
        return '<Audio {}>'.format(self.name)


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(228), index=True)
    filepath = db.Column(db.String(120), index=True, unique=True)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    active = db.Column(db.Boolean, index=True, default=False)
    
    def __repr__(self):
        return '<Program {}>'.format(self.name)


# modelo para las palabras
class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(32), index=True, unique=True)

    def __repr__(self):
        return '<Word {}>'.format(self.word)


# modelo para comandos pasados
class VoiceCommand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(256), index=True, unique=True)
    modified = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Voice Command {}>'.format(self.command)


# para las acciones
class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), index=True, default="")
    action = db.Column(db.String(64), index=True, default="")

    def __repr__(self):
        return '<Action {},{}>'.format(self.category, self.action)
