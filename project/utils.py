from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("login", next=request.path))
        if session.get("role") != "admin":
            flash("You don't have permission to access the admin dashboard.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)
    return wrapped

def allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def register_template_filters(app):
    @app.template_filter("dateformat")
    def dateformat(value, fmt="%b %d, %Y"):
        if not value:
            return "-"
        return value.strftime(fmt)

    @app.template_filter("timeformat")
    def timeformat(value, fmt="%I:%M %p"):
        if not value:
            return "-"
        return value.strftime(fmt).lstrip("0")

    @app.template_filter("d_size")
    def d_size_filter(num_bytes):
        size = float(num_bytes or 0)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


