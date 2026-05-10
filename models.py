from helpers.db import get_db_connection


def get_all_courses():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    conn.close()
    return courses


def get_all_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return students


def get_user_by_email_and_password(email, password):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password)
    ).fetchone()
    conn.close()
    return user


def get_student_id_by_user_id(user_id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT id FROM students WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return student["id"] if student else None