from flask import Flask, redirect, url_for, session

from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.course_routes import courses_bp
from routes.student_routes import students_bp
from routes.enrollment_routes import enrollment_bp


app = Flask(__name__)
app.secret_key = "auaf_secret_key"
class CurrentUser:
    @property
    def is_authenticated(self):
        return "username" in session

    @property
    def is_admin(self):
        return session.get("role") == "admin"

    @property
    def full_name(self):
        return session.get("full_name") or session.get("username") or "User"


@app.context_processor
def inject_globals():
    return {"current_user": CurrentUser()}


@app.route("/")
def root():
    return redirect(url_for("auth.login"))


app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(main_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(students_bp)
app.register_blueprint(enrollment_bp)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")