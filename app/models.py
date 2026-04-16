# app/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


def register_user_loader(login_manager):
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    UserMixin provides the methods Flask-Login needs:
    is_authenticated, is_active, is_anonymous, get_id.
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
