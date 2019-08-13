import datetime
import json
import os
import uuid

from flask_restful import Resource, abort, fields, marshal_with, reqparse

from app import app, db
from app.models import Program


class ProgramJson(fields.Raw):
    def format(self, filepath: str):
        content = {}
        with open(filepath) as f:
            content = json.load(f)
        return json.dumps(content)

program_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "description": fields.String,
    "content": ProgramJson(attribute="filepath"),
    "modified": fields.DateTime
}

program_parser = reqparse.RequestParser(bundle_errors=True)
program_parser.add_argument("name", required=True, help="Invalid name")
program_parser.add_argument("description", required=True, help="Invalid description")
program_parser.add_argument("content", type=json.loads, required=True, help="Invalid content")


class ProgramRes(Resource):
    def check_program(self, program):
        if not program:
            abort(404, message="program not found")

    @marshal_with(program_fields)
    def get(self, program_id: int):
        program = Program.query.filter_by(id=program_id).first()
        self.check_program(program)
        return program, 200

    @marshal_with(program_fields)
    def put(self, program_id: int):
        args = program_parser.parse_args()
        program = Program.query.filter_by(id=program_id).first()
        self.check_program(program)
        program.name = args["name"]
        program.description = args["description"]
        with open(program.filepath, "w") as f:
            json.dump(args["content"], f)
        program.modified = datetime.datetime.now()
        db.session.commit()
        return program, 201

    def delete(self, program_id: int):
        program = Program.query.filter_by(id=program_id).first()
        self.check_program(program)
        if os.path.exists(program.filepath):
            os.remove(program.filepath)
        db.session.delete(program)
        db.session.commit()
        return "", 204


class ProgramListRes(Resource):
    @marshal_with(program_fields)
    def get(self):
        programs = Program.query.all()
        return programs, 200

    @marshal_with(program_fields)
    def post(self):
        args = program_parser.parse_args()
        name = ".".join([uuid.uuid4().hex, datetime.date.today().isoformat(), "json"])
        filepath = os.path.join(app.config['PROGRAMS_FOLDER'], name)
        with open(filepath, "w") as f:
            json.dump(args["content"], f)
        program = Program(
            filepath=filepath,
            name=args["name"],
            description=args["description"],
        )
        db.session.add(program)
        db.session.commit()
        return program, 201
