from flask import render_template, make_response, jsonify
from app import app, db


# json format
@app.errorhandler(404)
def not_found_error(error):
    return make_response(jsonify({'error':'Not found'}), 404)

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
