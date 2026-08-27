import uuid
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def new_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    documents = db.relationship(
        "Document", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", backref="owner", lazy=True, cascade="all, delete-orphan"
    )



class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_category_user_name"),)


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    group_id = db.Column(db.String(36), nullable=False, default=new_uuid)
    version = db.Column(db.Integer, nullable=False, default=1)
    is_latest = db.Column(db.Boolean, nullable=False, default=True)

    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=True, default="Uncategorized")
    notes = db.Column(db.Text, nullable=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    filesize_bytes = db.Column(db.Integer, nullable=False, default=0)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

