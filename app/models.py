from datetime import datetime, timedelta
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, moscow_tz  # Убедитесь, что moscow_tz определен и импортирован


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    is_admin: so.Mapped[bool] = so.mapped_column(default=False)

    posts: so.Mapped[list['Post']] = so.relationship('Post', back_populates='author', lazy=True)

    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(moscow_tz))
    avatar: so.Mapped[str] = so.mapped_column(sa.String(120), default='default_avatar.png')

    # Удаляем дублирующееся поле likes и добавляем только одно
    likes: so.Mapped[list['Like']] = so.relationship('Like', back_populates='user', lazy=True)

    featured_posts: so.Mapped[list['FeaturedPosts']] = so.relationship('FeaturedPosts', back_populates='user',
                                                                       lazy=True)

    register_date: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(moscow_tz))

    def __repr__(self):
        return f'<User {self.username}>'

    def posts_count(self) -> int:
        return db.session.query(Post).filter_by(user_id=self.id).count()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def avatar_url(self) -> str:
        return url_for('static', filename='uploads/' + self.avatar)

    def total_likes(self) -> int:
        return db.session.query(sa.func.count(Like.id)).join(Post).filter(Post.user_id == self.id).scalar()

    def formatted_reg_date(self) -> Optional[str]:
        if self.register_date:
            return self.register_date.strftime("%d.%m.%Y")

    def formatted_last_seen(self) -> Optional[str]:
        if self.last_seen:
            return self.last_seen.strftime('%H:%M %d.%m.%Y')
        return None

    def is_liking(self, post: 'Post') -> bool:
        return db.session.query(Like).filter_by(post_id=post.id, user_id=self.id).count() > 0

    def is_featured(self, post: 'Post') -> bool:
        return db.session.query(FeaturedPosts).filter_by(post_id=post.id, user_id=self.id).count() > 0

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

    likes: so.Mapped[list['Like']] = so.relationship('Like', back_populates='post', lazy=True,
                                                     cascade="all, delete-orphan")

    featured_posts: so.Mapped[list['FeaturedPosts']] = so.relationship('FeaturedPosts', back_populates='post',
                                                                       lazy=True, cascade="all, delete-orphan")

    author: so.Mapped[User] = so.relationship('User', back_populates='posts')

    def __repr__(self):
        return f'<Post {self.body[:20]}>'

    def like_count(self) -> int:
        return db.session.query(Like).filter_by(post_id=self.id).count()

    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime('%d.%m.%Y %H:%M')


class Like(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('post.id'), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)

    post: so.Mapped[Post] = so.relationship('Post', back_populates='likes')
    user: so.Mapped[User] = so.relationship('User', back_populates='likes')

    def __repr__(self):
        return f'<Like {self.id}>'


class FeaturedPosts(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('post.id'), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)

    post: so.Mapped[Post] = so.relationship('Post', back_populates='featured_posts')
    user: so.Mapped[User] = so.relationship('User', back_populates='featured_posts')


@login.user_loader
def load_user(id: int) -> Optional[User]:
    return db.session.get(User, id)
