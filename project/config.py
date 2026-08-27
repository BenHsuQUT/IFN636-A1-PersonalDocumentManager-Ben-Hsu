import os
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_seccret")

    # ---- MySQL connection ----
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "00000000")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_DB = os.environ.get("MYSQL_DB", "personal_document_manager")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- File upload ----
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per request
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    # ---- Storage quotas ----
    USER_QUOTA_BYTES = 20 * 1024 * 1024 * 1024       # 20 GB / user
    ADMIN_TOTAL_QUOTA_BYTES = 500 * 1024 * 1024 * 1024  # 500 GB total
