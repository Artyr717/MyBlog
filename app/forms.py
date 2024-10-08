import sqlalchemy as sa
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp

from app import db
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                          message="Username must contain only Latin letters, numbers, and underscores.")])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                            message="Password must contain only Latin letters, numbers, and underscores.")])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                          message="Username must contain only Latin letters, numbers, and underscores.")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                            message="Password must contain only Latin letters, numbers, and underscores.")])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password'), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                                   message="Password must contain only Latin letters, numbers, and underscores.")])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Regexp(r'^[a-zA-Z0-9_]+$',
                                                                          message="Username must contain only Latin letters, numbers, and underscores.")])
    about_me = TextAreaField('About Me', validators=[Length(min=0)])
    avatar = FileField('Upload New Avatar (optional)')
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            # Создание запроса для проверки существования имени пользователя
            stmt = sa.select(User).where(User.username == username.data)
            user = db.session.scalars(stmt).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class CreatePostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    preview = StringField("Preview", validators=[DataRequired(), Length(min=10, max=100)])
    body = TextAreaField("Main Text", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Create')


class EditPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    preview = StringField("Preview", validators=[DataRequired(), Length(min=10, max=100)])
    body = TextAreaField("Main Text", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Submit')

    class EditPostForm(FlaskForm):
        def __init__(self, original_title, original_preview, original_body, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.title.data = original_title
            self.preview.data = original_preview
            self.body.data = original_body
