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

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def initial(self):
        return (self.username or "?")[0].upper()

    def total_storage_bytes(self):
        return sum(d.filesize_bytes for d in self.documents)

    def latest_documents(self):
        return (
            Document.query.filter_by(user_id=self.id, is_latest=True)
            .order_by(Document.uploaded_at.desc())
            .all()
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

    def relative_path(self):
        return f"{self.user_id}/{self.stored_filename}"

    def d_size(self):
        size = float(self.filesize_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def extension(self):
        return self.original_filename.rsplit(".", 1)[-1].lower() if "." in self.original_filename else ""

    def icon_label(self):
        ext = self.extension()
        return {
            "docx": "W", "doc": "W",
            "pdf": "PDF",
            "txt": "TXT"
        }.get(ext, ext.upper()[:3] or "FILE")

    def is_previewable_image(self):
        pass

    def is_previewable_pdf(self):
        pass

    def versions(self):
        return (
            Document.query.filter_by(group_id=self.group_id)
            .order_by(Document.version.desc())
            .all()
        )

    def is_recent(self, days=7):
        return self.uploaded_at and self.uploaded_at >= datetime.utcnow() - timedelta(days=days)
