from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask import jsonify, abort, make_response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User, Audio, Program

import os

ALLOWED_EXTENSIONS = set(['wav', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
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


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('no selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            print(request.form['tipo'])
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['AUDIOS_FOLDER'], filename)
            file.save(filepath)

            audio = Audio(name=filename, content=request.form['content'], filepath=filepath)
            db.session.add(audio)
            db.session.commit()

            return redirect(url_for('upload_file', filename=filename))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


### audio files
@app.route('/api/audios', methods=['GET'])
def get_audios():
    # fetch all audios and return a list
    audios = Audio.query.all()

    audios_list = []
    for audio in audios:
        audios_list.append(
            {
                'id':audio.id, 
                'name':audio.name, 
                'content':audio.content
            })
        # audios_dic[audio.id] = audio.filepath

    return jsonify(audios_list)

@app.route('/api/audios/<int:audio_id>', methods=['GET'])
def get_audio(audio_id):
    print(audio_id)
    audio = Audio.query.filter_by(id=audio_id).first()
    audio_dic = {'id':audio.id, 'name':audio.name, 'content':audio.content}
    return jsonify(audio_dic)


# @app.route('/api/audios', methods=['POST'])
# def create_audio():
#     if not request.json or not title




### audio files
@app.route('/api/programs', methods=['GET'])
def get_programs():
    # fetch all programs and return a list
    programs = Program.query.all()

    programs_list = []
    for program in programs:
        programs_list.append(
            {
                'id':program.id, 
                'name':program.name, 
                'description':program.description,
            })
        # programs_dic[program.id] = program.filepath

    return jsonify(programs_list)


@app.route('/api/programs/<int:program_id>', methods=['GET'])
def get_program(program_id):
    print(program_id)
    program = Program.query.filter_by(id=program_id).first()
    content = "nada por aqui" # TODO get content 
    program_dic = {
        'id':program.id, 
        'name':program.name, 
        'description':program.description,
        'content': content
        }
    return jsonify(program_dic)



@app.route('/api/programs', methods=['POST'])
def create_program():
    if not request.json or not 'id' in request.json:
        abort(400)
    
    program = 