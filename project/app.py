import os
import shutil
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for,session, flash, send_from_directory, abort
from werkzeug.utils import secure_filename

from project.config import Config
from project.models import db, User, Document, Category, new_uuid
from project.utils import login_required, admin_required, register_template_filters,allowed_file

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
register_template_filters(app)
# -------------------------------------------------------------------- getter --
def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}

# -------------------------------------------------------------------- auth --
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

# -------------------------------------------------------------------- user_dashboard --
@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("admin_dashboard" if session.get("role") == "admin" else "dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()

    all_latest = user.latest_documents()
    existing_names = {c.name for c in Category.query.filter_by(user_id=user.id).all()}
    doc_category_names = {d.category for d in all_latest if d.category and d.category != "Uncategorized"}
    missing_names = doc_category_names - existing_names
    if missing_names:
        for name in missing_names:
            db.session.add(Category(user_id=user.id, name=name))
        db.session.commit()

    categories = Category.query.filter_by(user_id=user.id).order_by(Category.name).all()

    total_storage = user.total_storage_bytes()
    quota = app.config["USER_QUOTA_BYTES"]
    percent_used = round((total_storage / quota) * 100, 1) if quota else 0
    recent_count = sum(1 for d in all_latest if d.is_recent())

    return render_template(
        "user_dashboard.html",
        docs=all_latest,
        all_docs=all_latest,
        categories=categories,
        total_documents=len(all_latest),
        total_storage=total_storage,
        percent_used=min(percent_used, 100),
        quota=quota,
        recent_count=recent_count,
        today=datetime.utcnow(),
    )

# -----------------------category--------------------------------
@app.route("/categories/add", methods=["POST"])
@login_required
def add_category():
    user = get_current_user()
    name = request.form.get("name", "").strip()

    if not name:
        flash("Category name can't be empty.", "error")
    elif name.lower() == "uncategorized":
        flash("That name is reserved.", "error")
    elif Category.query.filter(
        Category.user_id == user.id, db.func.lower(Category.name) == name.lower()
    ).first():
        flash(f'You already have a category named "{name}".', "error")
    else:
        db.session.add(Category(user_id=user.id, name=name))
        db.session.commit()
        flash(f'Category "{name}" added.', "success")

    return redirect(url_for("dashboard"))


@app.route("/categories/<int:category_id>/rename", methods=["POST"])
@login_required
def rename_category(category_id):
    user = get_current_user()
    category = Category.query.get_or_404(category_id)
    if category.user_id != user.id:
        abort(403)

    new_name = request.form.get("name", "").strip()
    old_name = category.name

    if not new_name:
        flash("Category name can't be empty.", "error")
    elif new_name.lower() == "uncategorized":
        flash("That name is reserved.", "error")
    elif new_name.lower() != old_name.lower() and Category.query.filter(
        Category.user_id == user.id, db.func.lower(Category.name) == new_name.lower()
    ).first():
        flash(f'You already have a category named "{new_name}".', "error")
    else:
        category.name = new_name
        Document.query.filter_by(user_id=user.id, category=old_name).update({"category": new_name})
        db.session.commit()
        flash(f'Renamed "{old_name}" to "{new_name}".', "success")

    return redirect(url_for("dashboard"))


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    user = get_current_user()
    category = Category.query.get_or_404(category_id)
    if category.user_id != user.id:
        abort(403)

    old_name = category.name
    Document.query.filter_by(user_id=user.id, category=old_name).update({"category": "Uncategorized"})
    db.session.delete(category)
    db.session.commit()
    flash(f'Deleted category "{old_name}".', "success")
    return redirect(url_for("dashboard"))

# -----------------------document crud--------------------------------
@app.route("/upload", methods=["POST"])
@login_required
def upload_document():
    user = get_current_user()
    file = request.files.get("file")

    if not file or file.filename == "":
        flash("Please choose a file to upload.", "error")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        flash("Unsupported file format.", "error")
        return redirect(url_for("dashboard"))

    version_of = request.form.get("version_of", "")
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip() or "Uncategorized"
    notes = request.form.get("notes", "").strip()

    ext = file.filename.rsplit(".", 1)[1].lower()
    user_folder = os.path.join(app.config["UPLOAD_FOLDER"], str(user.id))
    os.makedirs(user_folder, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(user_folder, stored_filename)
    file.save(filepath)
    filesize = os.path.getsize(filepath)


    parent = None
    if version_of:
        parent = Document.query.filter_by(id=version_of, user_id=user.id, is_latest=True).first()

    if parent:
        parent.is_latest = False
        new_version = parent.version + 1
        group_id = parent.group_id
        title = parent.title
        category = parent.category
    else:
        group_id = new_uuid()
        new_version = 1
        if not title:
            title = file.filename.rsplit(".", 1)[0]

    doc = Document(
        user_id=user.id, group_id=group_id, version=new_version, is_latest=True,
        title=title, category=category, notes=notes,
        original_filename=secure_filename(file.filename),
        stored_filename=stored_filename, filesize_bytes=filesize,
    )
    db.session.add(doc)
    db.session.commit()

    flash("Upload successful.", "success")
    return redirect(url_for("dashboard"))


@app.route("/documents/<int:doc_id>")
@login_required
def document_details(doc_id):
    doc = Document.query.get_or_404(doc_id)
    user = get_current_user()
    if doc.user_id != user.id and not user.is_admin:
        abort(403)
    versions = doc.versions()
    return render_template("document_details.html", doc=doc, versions=versions)


@app.route("/documents/<int:doc_id>/update", methods=["POST"])
@login_required
def update_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    user = get_current_user()
    if doc.user_id != user.id and not user.is_admin:
        abort(403)

    doc.title = request.form.get("title", doc.title).strip() or doc.title
    doc.category = request.form.get("category", doc.category).strip() or "Uncategorized"
    doc.notes = request.form.get("notes", "").strip()
    db.session.commit()
    flash("Document details updated.", "success")

    next_url = request.form.get("next", "")
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("document_details", doc_id=doc.id))

#check
@app.route("/documents/<int:doc_id>/download")
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    user = get_current_user()
    if doc.user_id != user.id and not user.is_admin:
        abort(403)
    directory = os.path.join(app.config["UPLOAD_FOLDER"], str(doc.user_id))
    
    return send_from_directory(directory, doc.stored_filename, as_attachment=True, download_name=doc.original_filename)

@app.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    user = get_current_user()
    if doc.user_id != user.id and not user.is_admin:
        abort(403)

    owner_id = doc.user_id
    group_docs = Document.query.filter_by(group_id=doc.group_id).all()
    for d in group_docs:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], str(d.user_id), d.stored_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(d)
    db.session.commit()

    flash("Document deleted.", "success")
    if user.is_admin and owner_id != user.id:
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("dashboard"))

# -------------------------------------------------------------------- admin_dashboard --
@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")