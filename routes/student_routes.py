from types import SimpleNamespace

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from helpers.db import (
    get_db_connection,
    table_exists,
    get_columns,
    first_existing,
    get_student_active_value,
    get_student_by_id,
)

from forms.forms import StudentEditForm



students_bp = Blueprint("students", __name__, url_prefix="/students")
@students_bp.route("/")
def list_students():
    """Display all students and support basic search."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if not table_exists("students"):
        return render_template("students/list.html", students=[], search="")

    search = request.args.get("search", "").strip()
    search_lower = search.lower()

    conn = get_db_connection()
    student_rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()

    enrolled_counts = {}
    if table_exists("enrollments"):
        enroll_cols = get_columns("enrollments")
        if "status" in enroll_cols:
            count_rows = conn.execute(
                """
                SELECT student_id, COUNT(*) AS total
                FROM enrollments
                WHERE status IS NULL OR status != 'dropped'
                GROUP BY student_id
                """
            ).fetchall()
        else:
            count_rows = conn.execute(
                """
                SELECT student_id, COUNT(*) AS total
                FROM enrollments
                GROUP BY student_id
                """
            ).fetchall()

        enrolled_counts = {row["student_id"]: row["total"] for row in count_rows}

    students = []

    for row in student_rows:
        full_name = first_existing(row, ["full_name", "name"], "")
        email = first_existing(row, ["email"], "")

        if not email and table_exists("users") and "user_id" in row.keys():
            user_row = conn.execute(
                "SELECT email FROM users WHERE id = ?",
                (row["user_id"],)
            ).fetchone()

            if user_row:
                email = user_row["email"]

        student_code = first_existing(row, ["student_id"], "")
        department = first_existing(row, ["department"], "")

        haystack = f"{full_name} {email} {student_code}".lower()
        if search_lower and search_lower not in haystack:
            continue

        students.append(
            SimpleNamespace(
                id=row["id"],
                full_name=full_name,
                email=email,
                student_id=student_code or f"S{row['id']:04d}",
                department=department or "Not Assigned",
                is_active=bool(get_student_active_value(row)),
                enrolled_count=enrolled_counts.get(row["id"], 0),
            )
        )

    conn.close()

    return render_template("students/list.html", students=students, search=search)


@students_bp.route("/<int:student_id>")
def view_student(student_id):
    """Display details for one student."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    student = get_student_by_id(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    return render_template("students/detail.html", student=student)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    """Allow an admin user to edit a student record."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can edit student records.", "danger")
        return redirect(url_for("students.list_students"))

    student = get_student_by_id(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("students.list_students"))

    form = StudentEditForm(student)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        student_code = request.form.get("student_id", "").strip()
        department = request.form.get("department", "").strip()
        is_active = 1 if request.form.get("is_active") else 0

        old_email = student.email

        conn = get_db_connection()
        student_cols = get_columns("students")

        update_parts = []
        update_values = []

        if "full_name" in student_cols:
            update_parts.append("full_name = ?")
            update_values.append(full_name)
        elif "name" in student_cols:
            update_parts.append("name = ?")
            update_values.append(full_name)

        if "email" in student_cols:
            update_parts.append("email = ?")
            update_values.append(email)

        if "student_id" in student_cols:
            update_parts.append("student_id = ?")
            update_values.append(student_code)

        if "department" in student_cols:
            update_parts.append("department = ?")
            update_values.append(department)

        if "is_active" in student_cols:
            update_parts.append("is_active = ?")
            update_values.append(is_active)

        if update_parts:
            update_values.append(student_id)
            conn.execute(
                f"UPDATE students SET {', '.join(update_parts)} WHERE id = ?",
                tuple(update_values),
            )

        if table_exists("users") and old_email:
            user_cols = get_columns("users")
            if "email" in user_cols:
                conn.execute(
                    "UPDATE users SET email = ? WHERE email = ?",
                    (email, old_email),
                )

        conn.commit()
        conn.close()

        flash("Student updated successfully.", "success")
        return redirect(url_for("students.view_student", student_id=student_id))

    return render_template("students/edit.html", student=student, form=form)

