import sqlite3
import os
from datetime import datetime
from types import SimpleNamespace

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(table_name):
    """Check whether a table exists in the database."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    conn.close()
    return row is not None


def get_columns(table_name):
    """Return a list of column names for a database table."""
    if not table_exists(table_name):
        return []
    conn = get_db_connection()
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    conn.close()
    return [row["name"] for row in rows]


def first_existing(row, names, default=None):
    """Return the first available value from a row using possible column names."""
    if row is None:
        return default
    for name in names:
        if name in row.keys():
            return row[name]
    return default


def parse_date(value):
    """Convert a database date value into a datetime object."""
    if not value:
        return datetime.now()

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    return datetime.now()
def get_user_full_name(user_row):
    """Find and return the user full name from related student data."""
    username = first_existing(user_row, ["username"], "User")
    email = first_existing(user_row, ["email"], "")

    if table_exists("students") and email:
        student_cols = get_columns("students")
        if "email" in student_cols:
            conn = get_db_connection()
            student = conn.execute(
                "SELECT * FROM students WHERE email = ?",
                (email,),
            ).fetchone()
            conn.close()
            if student:
                return first_existing(student, ["full_name", "name"], username)

    return username


def get_course_name_column():
    """Return the correct course name column used by the database."""
    cols = get_columns("courses")
    if "course_name" in cols:
        return "course_name"
    if "name" in cols:
        return "name"
    return None


def get_course_code_column():
    """Return the correct course code column used by the database."""
    cols = get_columns("courses")
    if "course_code" in cols:
        return "course_code"
    if "code" in cols:
        return "code"
    return None


def get_student_name_column():
    """Return the correct student name column used by the database."""
    cols = get_columns("students")
    if "full_name" in cols:
        return "full_name"
    if "name" in cols:
        return "name"
    return None


def get_enrollment_date_column():
    """Return the enrollment date column if it exists."""
    cols = get_columns("enrollments")
    for col in ["enrolled_at", "created_at", "date"]:
        if col in cols:
            return col
    return None


def get_student_active_value(row):
    """Return whether a student account is active."""
    if row is None:
        return 1

    keys = row.keys()
    if "is_active" in keys:
        return row["is_active"]
    if "active" in keys:
        return row["active"]
    if "status" in keys:
        status = str(row["status"]).lower()
        return 0 if status in ["inactive", "disabled"] else 1

    return 1


def get_enrolled_count(course_id):
    """Count how many active students are enrolled in a course."""
    if not table_exists("enrollments"):
        return 0

    conn = get_db_connection()
    enroll_cols = get_columns("enrollments")

    if "status" in enroll_cols:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM enrollments WHERE course_id = ? AND (status IS NULL OR status != 'dropped')",
            (course_id,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM enrollments WHERE course_id = ?",
            (course_id,),
        ).fetchone()

    conn.close()
    return row["total"] if row else 0


def make_course_object(row):
    """Convert a course database row into an object used by templates."""
    course_name = first_existing(row, ["course_name", "name"], "")
    course_code = first_existing(row, ["course_code", "code"], "")
    capacity = first_existing(row, ["capacity"], 0)

    try:
        capacity = int(capacity) if capacity is not None else 0
    except Exception:
        capacity = 0

    enrolled_count = get_enrolled_count(row["id"])
    available_seats = max(capacity - enrolled_count, 0)

    return SimpleNamespace(
        id=row["id"],
        course_name=course_name,
        name=course_name,
        course_code=course_code,
        instructor=first_existing(row, ["instructor"], ""),
        department=first_existing(row, ["department"], ""),
        schedule=first_existing(row, ["schedule"], ""),
        credits=first_existing(row, ["credits"], ""),
        capacity=capacity,
        description=first_existing(row, ["description"], ""),
        enrolled_count=enrolled_count,
        available_seats=available_seats,
        is_full=available_seats <= 0,
        is_available=True,
    )


def get_course_by_id(course_id):
    """Return a course object by course ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return make_course_object(row)


class EnrollmentList:
    """Small helper class that allows enrollment lists to be sorted in templates."""
    def __init__(self, items):
        self.items = items

    def order_by(self, field_name):
        reverse = False
        key_name = field_name

        if field_name.startswith("-"):
            reverse = True
            key_name = field_name[1:]

        sorted_items = sorted(
            self.items,
            key=lambda x: getattr(x, key_name, datetime.min) or datetime.min,
            reverse=reverse
        )
        return EnrollmentList(sorted_items)

    def all(self):
        return self.items


def get_student_by_id(student_id):
    """Return a student object with related enrollment information."""
    if not table_exists("students"):
        return None

    conn = get_db_connection()

    student_row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()

    if not student_row:
        conn.close()
        return None

    user_row = None
    if table_exists("users") and "user_id" in student_row.keys():
        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (student_row["user_id"],),
        ).fetchone()

    enrollments = []
    active_enrollments = []

    rows = conn.execute("""
        SELECT e.id AS enrollment_id, e.status, e.course_id,
               c.id AS real_course_id,
               c.course_code, c.course_name, c.credits, c.schedule
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.id DESC
    """, (student_id,)).fetchall()

    for row in rows:
        status = row["status"] or "enrolled"

        course_obj = SimpleNamespace(
            id=row["real_course_id"],
            course_code=row["course_code"],
            name=row["course_name"],
            credits=row["credits"],
            schedule=row["schedule"],
        )

        enrollment_obj = SimpleNamespace(
            id=row["enrollment_id"],
            status=status,
            enrolled_at=datetime.now(),
            course=course_obj,
        )

        enrollments.append(enrollment_obj)

        if status.lower() != "dropped":
            active_enrollments.append(enrollment_obj)

    conn.close()

    return SimpleNamespace(
        id=student_row["id"],
        full_name=student_row["full_name"],
        student_id=f"S{student_row['id']:04d}",
        department=student_row["department"] or "Not Assigned",
        username=user_row["username"] if user_row else "N/A",
        email=user_row["email"] if user_row and "email" in user_row.keys() else "N/A",
        created_at=datetime.now(),
        is_active=True,
        active_enrollments=active_enrollments,
        enrollments=EnrollmentList(enrollments),
    )
