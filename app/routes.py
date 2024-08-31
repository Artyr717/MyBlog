from datetime import datetime, timezone
from urllib.parse import urlsplit

import sqlalchemy as sa
from flask import render_template, url_for, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreatePostForm
from .models import User, Post


@app.route("/")
@app.route("/index")
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template("index.html", posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', "danger")
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.timestamp.desc()).paginate(page=page, per_page=4,
                                                                                       error_out=False)
    return render_template('user.html', user=user, posts=posts)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


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
        flash('Congratulations, you are now a registered user!', "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route("/create_post", methods=['GET', 'POST'])
@login_required
def create_post():
    if current_user.is_admin:
        form = CreatePostForm()
        if form.validate_on_submit():
            post = Post(title=form.title.data, body=form.body.data, write_comments=form.write_comments.data,
                        author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Congratulations, new post created!', "success")
            return redirect(url_for('index'))
        else:
            print(form.errors)  # Вывод ошибок валидации формы
        return render_template("create_post.html", form=form)

    return render_template("404.html")


@app.route("/post_detail/<post_id>")
@login_required
def post_detail(post_id):
    pass
