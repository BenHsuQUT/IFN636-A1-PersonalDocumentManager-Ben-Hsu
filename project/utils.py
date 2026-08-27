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



