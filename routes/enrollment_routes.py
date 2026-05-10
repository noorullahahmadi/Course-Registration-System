from models import get_student_id_by_user_id
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from helpers.db import get_db_connection

enrollment_bp = Blueprint("enrollment", __name__, url_prefix="/enrollment")


def get_student_id():
    user_id = session.get("user_id")
    return get_student_id_by_user_id(user_id)
    user_id = session.get("user_id")

    conn = get_db_connection()
    student = conn.execute(
        "SELECT id FROM students WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    return student["id"] if student else None


@enrollment_bp.route("/courses")
def student_courses():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    return render_template("students/courses.html", courses=courses)


@enrollment_bp.route("/enroll/<int:course_id>", methods=["POST"])
def enroll(course_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()
    if not student_id:
        flash("Student not found", "danger")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    
    existing = conn.execute("""
    SELECT * FROM enrollments
    WHERE student_id = ? 
    AND course_id = ? 
    AND status IN ('enrolled', 'completed')
""", (student_id, course_id)).fetchone()

    
    if existing:
        conn.close()
        flash("You already enrolled or completed this course.", "warning")
        return redirect(request.referrer)


    conn.execute("""
        INSERT INTO enrollments (student_id, course_id, status)
        VALUES (?, ?, 'enrolled')
    """, (student_id, course_id))

    conn.commit()
    conn.close()

    flash("Enrolled successfully!", "success")
    return redirect(request.referrer)


@enrollment_bp.route("/drop/<int:course_id>", methods=["POST"])
def drop(course_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()
    if not student_id:
        flash("Student not found", "danger")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE enrollments
        SET status = 'dropped'
        WHERE student_id = ? AND course_id = ? AND status = 'enrolled'
    """, (student_id, course_id))

    conn.commit()
    conn.close()

    flash("Course dropped", "info")
    return redirect(request.referrer)


@enrollment_bp.route("/complete/<int:course_id>", methods=["POST"])
def complete(course_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()
    if not student_id:
        flash("Student not found", "danger")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE enrollments
        SET status = 'completed'
        WHERE student_id = ? AND course_id = ? AND status = 'enrolled'
    """, (student_id, course_id))

    conn.commit()
    conn.close()

    flash("Course marked as completed!", "success")
    return redirect(url_for("enrollment.history"))


@enrollment_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    student_id = get_student_id()
    if not student_id:
        flash("Student not found", "danger")
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT e.id, e.status, c.course_name, c.course_code
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.id DESC
    """, (student_id,)).fetchall()

    conn.close()

    return render_template("students/history.html", enrollments=rows)