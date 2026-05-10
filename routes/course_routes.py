from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from helpers.db import (
    get_db_connection,
    get_columns,
    make_course_object,
    get_course_by_id,
)

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")

@courses_bp.route("/")
def list_courses():
    """Display all courses and allow filtering by search fields."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    rows = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    courses = [make_course_object(row) for row in rows]

    enrolled_rows = conn.execute("""
    SELECT course_id, status
    FROM enrollments
    WHERE student_id = (
        SELECT id FROM students WHERE user_id = ?
    )
    ORDER BY id DESC
""", (session["user_id"],)).fetchall()

    enrolled_map = {}

    for row in enrolled_rows:
        if row["course_id"] not in enrolled_map:
            enrolled_map[row["course_id"]] = row["status"]

    conn.close()


    query = request.args.get("query", "").strip().lower()
    department = request.args.get("department", "").strip().lower()
    instructor = request.args.get("instructor", "").strip().lower()

    filtered = []

    for course in courses:
        if query and query not in (course.course_name or "").lower() and query not in (course.course_code or "").lower():
            continue
        if department and department not in (course.department or "").lower():
            continue
        if instructor and instructor not in (course.instructor or "").lower():
            continue

        filtered.append(course)

    return render_template(
    "courses/list.html",
    courses=courses,
    enrolled_map=enrolled_map
)


@courses_bp.route("/add", methods=["GET", "POST"])
def add_course():
    """Allow an admin user to add a new course."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can add courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    if request.method == "POST":
        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        instructor = request.form.get("instructor", "").strip()
        department = request.form.get("department", "").strip()
        schedule = request.form.get("schedule", "").strip()
        credits = request.form.get("credits", "").strip()
        capacity = request.form.get("capacity", "").strip()
        description = request.form.get("description", "").strip()

        conn = get_db_connection()
        cols = get_columns("courses")

        if "course_code" in cols:
            existing = conn.execute(
                "SELECT * FROM courses WHERE course_code = ?",
                (course_code,),
            ).fetchone()
            if existing:
                conn.close()
                flash("You already enrolled or completed this course.", "warning")
                return redirect(request.referrer)

        insert_data = {}

        if "course_code" in cols:
            insert_data["course_code"] = course_code
        elif "code" in cols:
            insert_data["code"] = course_code

        if "course_name" in cols:
            insert_data["course_name"] = course_name
        elif "name" in cols:
            insert_data["name"] = course_name

        if "instructor" in cols:
            insert_data["instructor"] = instructor
        if "department" in cols:
            insert_data["department"] = department
        if "schedule" in cols:
            insert_data["schedule"] = schedule
        if "credits" in cols:
            insert_data["credits"] = credits
        if "capacity" in cols:
            insert_data["capacity"] = capacity
        if "description" in cols:
            insert_data["description"] = description

        columns_sql = ", ".join(insert_data.keys())
        placeholders = ", ".join(["?"] * len(insert_data))
        values = tuple(insert_data.values())

        conn.execute(
            f"INSERT INTO courses ({columns_sql}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        conn.close()

        flash("Course added successfully.", "success")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/form.html", course=None)


@courses_bp.route("/<int:course_id>")
def view_course(course_id):
    """Display details for one course."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.list_courses"))

    return render_template("courses/detail.html", course=course)


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    """Allow an admin user to edit an existing course."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can edit courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    course = get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.list_courses"))

    if request.method == "POST":
        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        instructor = request.form.get("instructor", "").strip()
        department = request.form.get("department", "").strip()
        schedule = request.form.get("schedule", "").strip()
        credits = request.form.get("credits", "").strip()
        capacity = request.form.get("capacity", "").strip()
        description = request.form.get("description", "").strip()

        conn = get_db_connection()
        cols = get_columns("courses")

        code_col = "course_code" if "course_code" in cols else ("code" if "code" in cols else None)
        if code_col:
            existing = conn.execute(
                f"SELECT * FROM courses WHERE {code_col} = ? AND id != ?",
                (course_code, course_id),
            ).fetchone()

            if existing:
                conn.close()
                flash("Another course already uses this course code.", "danger")
                return redirect(url_for("courses.edit_course", course_id=course_id))

        update_data = []

        if "course_code" in cols:
            update_data.append(("course_code", course_code))
        elif "code" in cols:
            update_data.append(("code", course_code))

        if "course_name" in cols:
            update_data.append(("course_name", course_name))
        elif "name" in cols:
            update_data.append(("name", course_name))

        if "instructor" in cols:
            update_data.append(("instructor", instructor))
        if "department" in cols:
            update_data.append(("department", department))
        if "schedule" in cols:
            update_data.append(("schedule", schedule))
        if "credits" in cols:
            update_data.append(("credits", credits))
        if "capacity" in cols:
            update_data.append(("capacity", capacity))
        if "description" in cols:
            update_data.append(("description", description))

        set_clause = ", ".join([f"{col} = ?" for col, _ in update_data])
        values = [value for _, value in update_data]
        values.append(course_id)

        conn.execute(
            f"UPDATE courses SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        conn.close()

        flash("Course updated successfully.", "success")
        return redirect(url_for("courses.view_course", course_id=course_id))

    return render_template("courses/form.html", course=course)


@courses_bp.route("/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    """Allow an admin user to delete a course."""
    if "username" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "admin":
        flash("Only admin can delete courses.", "danger")
        return redirect(url_for("courses.list_courses"))

    conn = get_db_connection()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

    flash("Course deleted successfully.", "success")
    return redirect(url_for("courses.list_courses"))
