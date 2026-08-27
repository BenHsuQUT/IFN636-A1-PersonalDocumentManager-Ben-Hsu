import os
import shutil
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for,session, flash, send_from_directory, abort
from werkzeug.utils import secure_filename

from project.config import Config
from project.models import db, User, Document, Category, new_uuid
from project.utils import login_required, admin_required

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}

@app.route("/register", methods=["GET", "POST"])
def register():
    pass

@app.route("/login", methods=["GET", "POST"])
def login():
    pass

@app.route("/logout")
def logout():
    return
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))