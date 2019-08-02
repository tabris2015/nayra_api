import datetime
from app import app, db
from flask_restful import Resource, fields, marshal_with, reqparse, abort
from app.models import AudioCategory


audio_category_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "modified": fields.DateTime
}

audio_category_parser = reqparse.RequestParser(bundle_errors=True)
audio_category_parser.add_argument("name", required=True, help="Invalid name")


class AudioCategoryRes(Resource):
    def check_audio_category(self, audio_category):
        if not audio_category:
            abort(404, message="audio category not found")

    @marshal_with(audio_category_fields)
    def get(self, ac_id: int):
        audio_category = AudioCategory.query.filter_by(id=ac_id).first()
        self.check_audio_category(audio_category)
        return audio_category, 200

    @marshal_with(audio_category_fields)
    def put(self, ac_id: int):
        args = audio_category_parser.parse_args()
        audio_category = AudioCategory.query.filter_by(id=ac_id).first()
        self.check_audio_category(audio_category)
        audio_category.name = args["name"]
        audio_category.modified = datetime.datetime.now()
        db.session.commit()
        return audio_category, 201

    def delete(self, ac_id: int):
        audio_category = AudioCategory.query.filter_by(id=ac_id).first()
        self.check_audio_category(audio_category)
        db.session.delete(audio_category)
        db.session.commit()
        return '', 204


class AudioCategoryListRes(Resource):
    @marshal_with(audio_category_fields)
    def get(self):
        audio_categories = AudioCategory.query.all()
        return audio_categories, 200

    @marshal_with(audio_category_fields)
    def post(self):
        args = audio_category_parser.parse_args()
        audio_category = AudioCategory(name=args["name"])
        db.session.add(audio_category)
        db.session.commit()
        return audio_category, 201
