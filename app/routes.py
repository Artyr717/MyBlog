import os
from datetime import datetime
from urllib.parse import urlsplit

import sqlalchemy as sa
from flask import render_template, url_for, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from user_agents import parse
from werkzeug.utils import secure_filename

from app import app, db, moscow_tz
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreatePostForm, EditPostForm
from .models import User, Post, Like


@app.route("/")
@app.route("/index")
def index():
    user_agent = parse(request.headers.get('User-Agent'))
    if user_agent.is_mobile:
        template = 'mobile_index.html'
    else:
        template = 'desktop_index.html'
    page = request.args.get("page", 1, type=int)
    per_page = 5
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(template, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
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
        current_user.last_seen = datetime.now(moscow_tz)
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

        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(app.static_folder, 'uploads')

                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                current_user.avatar = filename

        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('user', username=current_user.username))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form, user=current_user)


@app.route("/create_post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        print(f"current_user: {current_user}, current_user.id: {current_user.id}")
        # Проверяем, что current_user существует и корректно загружен
        if current_user.is_authenticated:
            post = Post(title=form.title.data, body=form.body.data, preview=form.preview.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Поздравляем, новый пост создан!', "success")
            return redirect(url_for('index'))
        else:
            flash('Ошибка: пользователь не аутентифицирован', 'danger')
            return redirect(url_for('login'))
    else:
        print(form.errors)  # Вывод ошибок для отладки
    return render_template("create_post.html", form=form)


@app.route("/post_detail/<post_id>")
@login_required
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    print(f"Post.likes: {post.likes}")
    return render_template("post_details.html", post=post)


@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('index'))

    form = EditPostForm(
        original_title=post.title,
        original_preview=post.preview,
        original_body=post.body
    )

    if form.validate_on_submit():
        post.title = form.title.data
        post.preview = form.preview.data
        post.body = form.body.data
        db.session.commit()
        flash('Your post has been updated.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    if request.method == 'GET':
        form.title.data = post.title
        form.preview.data = post.preview
        form.body.data = post.body

    return render_template('edit_post.html', title='Edit Post', form=form, post=post)


@app.route("/delete_post/<int:post_id>", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('index'))

    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting post: {str(e)}', 'danger')

    return redirect(url_for('user', username=current_user.username))


@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_liking(post):
        # Если пользователь уже лайкнул пост, убираем лайк
        like = db.session.scalar(sa.select(Like).where(Like.post_id == post_id, Like.user_id == current_user.id))
        db.session.delete(like)
        flash('Removed your like.', 'success')
    else:
        # Если пользователь не лайкал пост, добавляем лайк
        like = Like(post_id=post_id, user_id=current_user.id)
        db.session.add(like)
        flash('You liked the post.', 'success')

    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))
