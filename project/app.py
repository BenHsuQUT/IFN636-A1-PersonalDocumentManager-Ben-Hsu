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
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = []
        if not username or not email or not password:
            errors.append("Please fill in all fields.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("This username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("This email is already registered.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", username=username, email=email)

        user = User(username=username, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully, please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", username="", email="")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Incorrect username or password.", "error")
        elif not user.is_active_account:
            flash("This account has been deactivated. Please contact an administrator.", "error")
        else:
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            user.last_login_at = datetime.utcnow()
            db.session.commit()

            flash(f"Welcome back, {user.username}!", "success")
            next_url = request.args.get("next")
            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            return redirect(next_url or url_for("dashboard"))

    return render_template("login.html", username="")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("user_dashboard.html")

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")