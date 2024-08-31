from datetime import datetime, timezone
from hashlib import md5
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_admin: so.Mapped[bool] = so.mapped_column(default=False)
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='author')
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def formatted_last_seen(self):
        if self.last_seen:
            return self.last_seen.strftime('%d.%m.%Y %H:%M')
        return None


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(120))
    body: so.Mapped[str] = so.mapped_column(sa.String(420))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    write_comments: so.Mapped[bool] = so.mapped_column(default=False)
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='post')
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def formatted_timestamp(self):
        return self.timestamp.strftime('%d.%m.%Y %H:%M')


class Comment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    content: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id), index=True)
    post: so.Mapped['Post'] = so.relationship(back_populates='comments')
    author: so.Mapped[User] = so.relationship(back_populates='comments')

    def __repr__(self):
        return '<Comment {}>'.format(self.content)

    def formatted_timestamp(self):
        return self.timestamp.strftime('%d.%m.%Y %H:%M')


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
