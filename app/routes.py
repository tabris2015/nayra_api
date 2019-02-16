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
from app.models import User, Audio, Program, Word, Action
from app.fsm_parser import JsonFsm

ALLOWED_EXTENSIONS = {'wav'}

fsm = JsonFsm()


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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/audios', methods=['POST'])
def create_audio():
    # check
    if 'file' not in request.files:
        flash('No file part')
        return jsonify({'result': 'no file'}), 403

    file = request.files['file']

    if file.filename == '':
        flash('no selected file')
        return jsonify({'result': 'no filename'}), 403

    audio_file = Audio.query.filter_by(name=file.filename).first()

    if audio_file:
        return jsonify({'result': 'filename already exists'}), 403

    if file and allowed_file(file.filename):
        print(request.form['category'])

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['AUDIOS_FOLDER'], filename)
        file.save(filepath)

        audio = Audio(
            name=filename, 
            content=request.form['content'], 
            filepath=filepath, 
            category=request.form['category'])
            
        db.session.add(audio)
        db.session.commit()

        return jsonify({'id': audio.id, 'name': audio.name, 'content': audio.content}), 201

    else:
        return jsonify({'result': 'invalid extension'}), 403


# audio files
@app.route('/api/audios', methods=['GET'])
def get_audios():
    # fetch all audios and return a list
    audios = Audio.query.all()

    audios_list = []
    for audio in audios:
        audios_list.append(
            {
                'id': audio.id,
                'name': audio.name,
                'content': audio.content,
                'category': audio.category
            })
        # audios_dic[audio.id] = audio.filepath

    return jsonify(audios_list)


@app.route('/api/audios/<int:audio_id>', methods=['GET'])
def get_audio(audio_id):
    print(audio_id)
    audio = Audio.query.filter_by(id=audio_id).first()
    if not audio:
        return jsonify({'result': 'no file'}), 404

    audio_dic = {'id': audio.id, 
                    'name': audio.name, 
                    'content': audio.content,
                    'category': audio.category}
    return jsonify(audio_dic)


##
# update a audio
@app.route('/api/audios/<int:audio_id>', methods=['PUT'])
def update_audio(audio_id):
    if not request.json:
        return jsonify({'result': 'no json'}), 403

    if not request.json['content']:
        return jsonify({'result': 'no content'}), 403

    audio = Audio.query.filter_by(id=audio_id).first()
    if not audio:
        return jsonify({'result': 'no file'}), 404

    audio.content = request.json['content']
    db.session.commit()

    return jsonify({'id': audio.id, 'name': audio.name, 'content': audio.content}), 200


@app.route('/api/audios/<int:audio_id>', methods=['DELETE'])
def delete_audio(audio_id):
    audio = Audio.query.filter_by(id=audio_id).first()

    if not audio:
        return jsonify({'result': 'no file'}), 404

    if os.path.exists(audio.filepath):
        os.remove(audio.filepath)

    db.session.delete(audio)
    db.session.commit()

    return jsonify({'result': 'success'})


### program files

# get all programs list
@app.route('/api/programs', methods=['GET'])
def get_programs():
    # fetch all programs and return a list
    programs = Program.query.all()

    programs_list = []
    for program in programs:
        programs_list.append(
            {
                'id': program.id,
                'name': program.name,
                'description': program.description,
                'modified': program.modified.strftime("%d/%m/%Y")
            })
        # programs_dic[program.id] = program.filepath

    return jsonify(programs_list), 200


# get a single complete program
@app.route('/api/programs/<int:program_id>', methods=['GET'])
def get_program(program_id):
    print(program_id)
    program = Program.query.filter_by(id=program_id).first()

    if not program:
        return jsonify({'result': 'no file'}), 404

    filepath = program.filepath
    content = "nada por aqui"  # TODO get content

    with open(filepath) as json_file:
        content = json.load(json_file)

    program_dic = {
        'id': program.id,
        'name': program.name,
        'description': program.description,
        'modified': program.modified.strftime("%d/%m/%Y"),
        'content': content
    }
    return jsonify(program_dic)


# create a program
@app.route('/api/programs', methods=['POST'])
def create_program():
    if not request.json or not 'name' in request.json:
        abort(400)

    programs = Program.query.all()

    if not programs:
        last_id = 1
    else:
        last_id = Program.query.order_by('-id').first().id

    new_id = last_id + 1

    content = request.json['content']

    # print(content)

    filename = str(new_id) + '.json'
    filepath = os.path.join(app.config['PROGRAMS_FOLDER'], filename)

    # save json file
    with open(filepath, 'w') as out:
        json.dump(content, out)

    program = Program(
        id=new_id,
        name=request.json['name'],
        description=request.json['description'],
        filepath=filepath
    )
    # save to db
    db.session.add(program)
    db.session.commit()

    program = Program.query.filter_by(id=new_id).first()
    program_dic = {
        'id': program.id,
        'name': program.name,
        'description': program.description,
        'modified': program.modified.strftime("%d/%m/%Y")
    }
    return jsonify(program_dic), 201


# update a program
@app.route('/api/programs/<int:program_id>', methods=['PUT'])
def update_program(program_id):
    if not request.json:
        return jsonify({'result': 'no json'}), 403

    if not request.json['content']:
        return jsonify({'result': 'no content'}), 403

    program = Program.query.filter_by(id=program_id).first()
    if not program:
        return jsonify({'result': 'no file'}), 404

    if 'name' in request.json:
        program.name = request.json['name']
        print('new name: {}'.format(request.json['name']))

    if 'description' in request.json:
        program.description = request.json['description']
        print('new description: {}'.format(request.json['description']))

    # save json file
    if 'content' in request.json:
        # update file
        filepath = program.filepath
        if os.path.exists(filepath):
            os.remove(filepath)

        content = request.json['content']
        with open(filepath, 'w') as out:
            json.dump(content, out)
        print('new program')

    db.session.commit()

    program_dic = {
        'id': program.id,
        'name': program.name,
        'description': program.description,
        'modified': program.modified.strftime("%d/%m/%Y")
    }
    return jsonify(program_dic), 200


@app.route('/api/programs/<int:program_id>', methods=['DELETE'])
def delete_program(program_id):
    program = Program.query.filter_by(id=program_id).first()

    if not program:
        return jsonify({'result': 'no file'}), 404

    if os.path.exists(program.filepath):
        os.remove(program.filepath)

    db.session.delete(program)
    db.session.commit()

    return jsonify({'result': 'success'})


@app.route('/api/programs/<int:program_id>/run', methods=['GET'])
def run_program(program_id):
    global fsm
    # global fsm
    program = Program.query.filter_by(id=program_id).first()

    if not program:
        return jsonify({'result': 'no file'}), 404

    print('corriendo {}'.format(program.name))
    active_programs = Program.query.filter_by(active=True).first()

    if active_programs:
        active_id = active_programs.id
        return jsonify({'result': 'a program is already running', 'id': active_id}), 403
    # fsm = 0

    # db.session.commit()
    fsm.loadFSM(program.filepath).begin()
    # run_program_async(program.filepath)
    # Thread(target=run_program_async, args=(program.filepath,)).start()
    # program.active = True
    return jsonify({'result': 'success'}), 200


@app.route('/api/programs/stop', methods=['GET'])
def stop_program():
    # global fsm
    print('deteniendo')
    program = Program.query.filter_by(active=True).first()

    if not program:
        return jsonify({'result': 'no program running'}), 404
    else:
        program.active = False
        db.session.commit()

        try:
            # fsm.trigger('kill')
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
        actions_list.append(
            {
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

    action_dic = {'id': action.id,
                    'category': action.category,
                    'action': action.action
                  }
    return jsonify(action_dic)
