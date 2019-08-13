import os
import json
from threading import Thread

from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask import jsonify, abort, make_response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User, Audio, Program, Word, Action, AudioCategory
from app.fsm_parser import JsonFsm, Robot

ALLOWED_EXTENSIONS = {'wav', 'mp3'}

fsm = JsonFsm()
running_instance = Robot({})


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/api/programs/<int:program_id>/run', methods=['GET'])
def run_program(program_id):
    global fsm
    global running_instance

    program = Program.query.filter_by(id=program_id).first()

    if not program:
        return jsonify({'result': 'no file'}), 404

    print('corriendo {}'.format(program.name))

    active_programs = Program.query.filter_by(active=True).first()

    if active_programs:
        active_id = active_programs.id

        if running_instance.isRunning():
            return jsonify({'result': 'a program is already running', 'id': active_id}), 403
        else:
            old_program = Program.query.filter_by(id=program_id).first()
            old_program.active = False
    # fsm = 0

    # db.session.commit()
    return_data = {"success": False}
    code = 500
    try:
        program.active = True
        db.session.commit()
        running_instance = fsm.loadFSM(program.filepath)
        running_instance.begin()
        program.active = False
        db.session.commit()
        return_data["success"] = True
        code = 200
    except Exception as exc:
        return_data["error"] = str(exc)
        app.logger.error(exc)
        program.active = False
        db.session.commit()

    return jsonify(return_data), code


@app.route('/api/programs/stop', methods=['GET'])
def stop_program():
    # global fsm
    global running_instance
    print('deteniendo')
    program = Program.query.filter_by(active=True).first()

    if not program:
        return jsonify({'result': 'no program running'}), 404
    else:
        program.active = False
        db.session.commit()

        try:
            running_instance.trigger('kill')
            return jsonify({'result': 'program stopped'}), 200
        except:
            return jsonify({'result': 'not stopped'}), 404


@app.route('/api/words', methods=['GET'])
def get_words():
    words = Word.query.all()
    words_list = [w.word for w in words]

    return jsonify(words_list), 200


@app.route('/api/words/<string:hint>', methods=['GET'])
def get_candidates(hint):
    candidates = Word.query.filter(Word.word.like(hint + '%'))

    candidates_list = []

    for candidate in candidates:
        candidates_list.append(candidate.word)
    #
    # if not candidates:
    #     return jsonify({'result': 'no file'}), 404
    #
    # audio_dic = {'id': audio.id, 'name': audio.name, 'content': audio.content}
    return jsonify(candidates_list)


# actions

@app.route('/api/actions', methods=['GET'])
def get_actions():
    # fetch all audios and return a list
    actions = Action.query.all()

    actions_list = []

    for action in actions:
        actions_list.append({
            'id': action.id,
            'category': action.category,
            'action': action.action
        })
        # audios_dic[audio.id] = audio.filepath

    return jsonify(actions_list)


@app.route('/api/actions/<int:action_id>', methods=['GET'])
def get_action(action_id):
    action = Action.query.filter_by(id=action_id).first()

    if not action:
        return jsonify({'result': 'no action'}), 404

    action_dic = {
        'id': action.id,
        'category': action.category,
        'action': action.action
    }
    return jsonify(action_dic)
