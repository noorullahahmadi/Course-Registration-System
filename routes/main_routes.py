from types import SimpleNamespace

from flask import Blueprint, render_template, redirect, url_for, session, request

from helpers.db import (
    get_db_connection,
    table_exists,
    get_course_name_column,
    get_course_code_column,
    get_student_name_column,
    get_enrollment_date_column,
    get_columns,
    parse_date,
)


main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
def dashboard():
    """Display the admin dashboard with system statistics."""

    if session.get("role") != "admin":
        return redirect(url_for("main.student_dashboard"))

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    total_students = 0
    total_courses = 0
    total_enrollments = 0

    if table_exists("students"):
        total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    if table_exists("courses"):
        total_courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]

    if table_exists("enrollments"):
        total_enrollments = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]

    stats = {
        "total_students": total_students,
        "total_courses": total_courses,
        "active_courses": total_courses,
        "total_enrollments": total_enrollments,
    }

    recent_enrollments = []

    if table_exists("students") and table_exists("courses") and table_exists("enrollments"):
        course_name_col = get_course_name_column()
        course_code_col = get_course_code_column()
        student_name_col = get_student_name_column()
        date_col = get_enrollment_date_column()
        enroll_cols = get_columns("enrollments")

        status_select = "enrollments.status AS status" if "status" in enroll_cols else "'enrolled' AS status"
        date_select = f"enrollments.{date_col} AS enrolled_at" if date_col else "NULL AS enrolled_at"
        student_name_select = f"students.{student_name_col} AS student_name" if student_name_col else "'Unknown Student' AS student_name"
        course_name_select = f"courses.{course_name_col} AS course_name" if course_name_col else "'Unnamed Course' AS course_name"
        course_code_select = f"courses.{course_code_col} AS course_code" if course_code_col else "'' AS course_code"

        query = f"""
            SELECT
                enrollments.id AS enrollment_id,
                {status_select},
                {date_select},
                students.id AS student_id,
                {student_name_select},
                courses.id AS course_id,
                {course_code_select},
                {course_name_select}
            FROM enrollments
            JOIN students ON enrollments.student_id = students.id
            JOIN courses ON enrollments.course_id = courses.id
            ORDER BY enrollments.id DESC
            LIMIT 5
        """

        rows = conn.execute(query).fetchall()

        for row in rows:
            recent_enrollments.append(
                SimpleNamespace(
                    id=row["enrollment_id"],
                    status=row["status"] or "enrolled",
                    enrolled_at=parse_date(row["enrolled_at"]),
                    student=SimpleNamespace(
                        id=row["student_id"],
                        full_name=row["student_name"],
                    ),
                    course=SimpleNamespace(
                        id=row["course_id"],
                        course_code=row["course_code"],
                        name=row["course_name"],
                    ),
                )
            )

    conn.close()

    return render_template(
        "main/admin_dashboard.html",
        stats=stats,
        recent_enrollments=recent_enrollments,
    )


@main_bp.route("/student-dashboard")
def student_dashboard():
    """Display the student dashboard with enrolled and available courses."""

    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "student":
        return redirect(url_for("main.dashboard"))

    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students
        WHERE user_id = ?
    """, (session.get("user_id"),)).fetchone()

    if not student:
        conn.close()
        return "Student profile not found"

    student_id = student["id"]

    enrolled_courses = conn.execute("""
        SELECT
            c.id,
            c.course_name,
            c.course_code,
            c.instructor,
            c.credits,
            c.schedule,
            e.status
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.student_id = ?
        AND e.status = 'enrolled'
    """, (student_id,)).fetchall()

    all_courses = conn.execute("""
        SELECT * FROM courses
    """).fetchall()

    conn.close()

    active_tab = request.args.get("tab", "enrolled")

    return render_template(
        "main/student_dashboard.html",
        student=student,
        enrolled_courses=enrolled_courses,
        all_courses=all_courses,
        active_tab=active_tab,
    )