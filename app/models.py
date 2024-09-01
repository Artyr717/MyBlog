from datetime import datetime, timedelta
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, moscow_tz  # Ensure moscow_tz is correctly defined and imported


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_admin: so.Mapped[bool] = so.mapped_column(default=False)

    # Указываем uselist=True (по умолчанию), т.к. отношение один ко многим
    posts: so.Mapped[list['Post']] = so.relationship('Post', back_populates='author', lazy=True)

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(moscow_tz))
    avatar: so.Mapped[str] = so.mapped_column(sa.String(120), default='default_avatar.png')

    # Отношение один ко многим с лайками
    likes: so.Mapped[list['Like']] = so.relationship('Like', back_populates='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def avatar_url(self) -> str:
        return url_for('static', filename='uploads/' + self.avatar)

    def formatted_last_seen(self) -> Optional[str]:
        if self.last_seen:
            return self.last_seen.strftime('%H:%M %d.%m.%Y')
        return None

    def is_liking(self, post: 'Post') -> bool:
        return db.session.query(Like).filter_by(post_id=post.id, user_id=self.id).count() > 0

    @property
    def is_online(self) -> bool:
        now = datetime.now(moscow_tz)
        if self.last_seen:
            if self.last_seen.tzinfo is None:
                self.last_seen = moscow_tz.localize(self.last_seen)
            return (now - self.last_seen) < timedelta(minutes=1)
        return False


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(60))
    preview: so.Mapped[str] = so.mapped_column(sa.String(120))
    body: so.Mapped[str] = so.mapped_column(sa.String(420), nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=datetime.now)

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)

    # Добавляем cascade="all, delete-orphan" для автоматического удаления лайков при удалении поста
    likes: so.Mapped[list['Like']] = so.relationship('Like', back_populates='post', lazy=True,
                                                     cascade="all, delete-orphan")

    author: so.Mapped[User] = so.relationship('User', back_populates='posts')

    def __repr__(self):
        return f'<Post {self.body[:20]}>'

    def like_count(self) -> int:
        return db.session.query(Like).filter_by(post_id=self.id).count()

    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime('%d.%m.%Y %H:%M')


class Like(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    # Внешний ключ к посту
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('post.id'), index=True)

    # Внешний ключ к пользователю
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)

    # Связь с постом и пользователем
    post: so.Mapped[Post] = so.relationship('Post', back_populates='likes')
    user: so.Mapped[User] = so.relationship('User', back_populates='likes')

    def __repr__(self):
        return f'<Like {self.id}>'


@login.user_loader
def load_user(id: int) -> Optional[User]:
    return db.session.get(User, id)
