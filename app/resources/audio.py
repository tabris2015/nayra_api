import datetime
import os

from flask_restful import Resource, abort, fields, marshal_with, reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app import app, db
from app.models import Audio, AudioCategory


ALLOWED_EXTENSIONS = ["wav", "mp3"]

audio_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "content": fields.String,
    "category_id": fields.Integer,
    "modified": fields.DateTime
}

def audio_type(file: FileStorage):
    if str.isalnum(file.filename):
        raise ValueError("invalid filename")
    elif file.filename.split(".")[-1].lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("file type not allowed")
    else:
        audio_file = Audio.query.filter_by(name=file.filename).first();
        if audio_file:
            raise ValueError("audio file already exists with id {id}".format(id=audio_file.id))
        else:
            return file

audio_parser = reqparse.RequestParser(bundle_errors=True)
audio_parser.add_argument("file", type=audio_type, location="files", help="Invalid audio file: {error_msg}")
audio_parser.add_argument("content", required=True, help="Invalid content")
audio_parser.add_argument("category_id", type=int, required=True, help="Invalid category id")


class AudioRes(Resource):
    def check_audio(self, audio):
        if not audio:
            abort(404, message="audio not found")

    @marshal_with(audio_fields)
    def get(self, audio_id: int):
        audio = Audio.query.filter_by(id=audio_id).first()
        self.check_audio(audio)
        return audio, 200

    @marshal_with(audio_fields)
    def put(self, audio_id: int):
        args = audio_parser.parse_args()
        audio = Audio.query.filter_by(id=audio_id).first()
        self.check_audio(audio)
        category = AudioCategory.query.filter_by(id=args["category_id"]).first()
        if not category:
            abort(400, message={"category_id": "audio category not found"})
        audio.content = args["content"]
        audio.category = category
        audio.modified = datetime.datetime.now()
        db.session.commit()
        return audio, 201

    def delete(self, audio_id: int):
        audio = Audio.query.filter_by(id=audio_id).first()
        self.check_audio(audio)
        if os.path.exists(audio.filepath):
            os.remove(audio.filepath)
        db.session.delete(audio)
        db.session.commit()
        return "", 204


class AudioListRes(Resource):
    @marshal_with(audio_fields)
    def get(self):
        audios = Audio.query.all()
        return audios, 200

    @marshal_with(audio_fields)
    def post(self):
        args = audio_parser.parse_args()
        category = AudioCategory.query.filter_by(id=args["category_id"]).first()
        if not category:
            abort(400, message={"category_id": "audio category not found"})
        if not args["file"]:
            abort(400, message={"file": "audio file required"})
        file = args["file"]
        name = secure_filename(file.filename)
        filepath = os.path.join(app.config['AUDIOS_FOLDER'], name)
        file.save(filepath)
        audio = Audio(
            name=name,
            filepath=filepath,
            content=args["content"],
            category=category
        )
        db.session.add(audio)
        db.session.commit()
        return audio, 201
