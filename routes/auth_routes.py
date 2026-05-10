from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from helpers.db import get_db_connection, first_existing, get_user_full_name
from forms.forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and redirect users based on their role."""
    form = LoginForm()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            role = first_existing(user, ["role"], "student")

            # Store user information in the session after successful login.
            session["user_id"] = user["id"]
            session["username"] = first_existing(user, ["username"], "")
            session["role"] = role
            session["full_name"] = get_user_full_name(user)
            session["email"] = first_existing(user, ["email"], "")

            if role == "admin":
                return redirect(url_for("main.dashboard"))
            else:
                return redirect(url_for("main.student_dashboard"))

        flash("Invalid email or password", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html", form=form)



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle new student registration."""

    form = RegisterForm()

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (username, password, role, email)
                VALUES (?, ?, 'student', ?)
            """, (username, password, email))

            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute("""
                INSERT INTO students (user_id, full_name, department)
                VALUES (?, ?, ?)
            """, (user_id, full_name, department))

            conn.commit()
            flash("Account created successfully! You can now log in.", "success")

        finally:
            conn.close()

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)

@auth_bp.route("/logout")
def logout():
    """Log out the current user."""
    session.clear()
    return redirect(url_for("auth.login"))
