# Course-Registration-System
A web-based system that allows students to register for courses and administrators to manage academic data efficiently.
## Project Details

- **Course:** Intro to Python  
- **Framework:** Flask 3.1.3  
- **Language:** Python 3  
- **Frontend:** HTML, CSS, JavaScript  
- **Database:** SQLite (SQL)  
- **Team:** Ghazal Ahmadzai, Faiza Hussaini, Noorullah Ahmadi, Parwana Jafari, Sana Hashemi  

## Project Overview

This is a web-based Student Course Registration System built using Python Flask and SQLite. It supports two types of users: Admins and Students. Admins can manage courses and students, while students can browse, search, and enroll in courses. The system also tracks enrollment history for each student.


## Project Structure

The project is organized into one main folder with separate modules for routes, helpers, forms, and models. The routes folder contains separate files for each feature: auth_routes.py handles login, registration, and logout. course_routes.py handles course management. enrollment_routes.py handles enrollment. main_routes.py handles dashboards. student_routes.py handles student management. The helpers folder contains db.py which handles all database connections and query functions. The forms folder contains forms.py with the login and register forms. models.py contains reusable database query functions. The static folder holds the CSS and JavaScript files for styling and interactivity. The templates folder contains all the HTML pages organized into subfolders for authentication, courses, the main dashboard, and student pages.


## Setup & Installation

To run this project on your machine, follow these steps. First, make sure you have Python 3.8 or higher installed. Then clone or download the project repository to your computer. Next, open a terminal inside the project folder and create a virtual environment by running python -m venv .venv. Activate it — on Windows use .venv\Scripts\activate, and on Mac or Linux use source .venv/bin/activate. After activating the environment, install Flask by running pip install flask. Finally, go into the project folder and run python app.py. The application will start and you can open it in your browser at http://127.0.0.1:5000.

## Sample Login Accounts

### Admin
- Email: admin1@gmail.com  
- Password: 1111  

### Student
- Email: ghazal.ahmadzai@auaf.edu.af  
- Password: 123  

Students can also create new accounts using the registration page.


## Database Schema

The database uses SQLite and has four tables. The users table stores all accounts in the system, whether admin or student. Each record has an ID, username, email, password, and a role field that is either "admin" or "student". The students table stores extra profile information for student users. It links to the users table through a user ID, and also stores the student's full name and department. The courses table holds all available courses. Each course has a course code, name, instructor, number of credits, schedule, department, capacity, and description. The enrollments table connects students to courses. Each record stores the student ID, the course ID, and the current status of the enrollment, such as "enrolled" or "dropped". One student can have many enrollments, and one course can have many students enrolled in it.


## API Endpoints

The application has five route groups. Authentication handles login at /auth/login, registration at /auth/register, and logout at /auth/logout. Dashboards — the admin dashboard is at /dashboard and shows system statistics and the 5 most recent enrollments. The student dashboard is at /student-dashboard and shows enrolled courses and all available courses in separate tabs. Courses are managed under /courses where admins can add, edit, and delete courses and all users can view and search them. Student management is under /students and is admin only. Enrollment routes are under /enrollment and are for students only, allowing them to browse, search, enroll, drop, and view their enrollment history.


## Data Models

After login, the application stores the user's ID, username, role, full name, and email in a Flask session. This session data controls what each user can see and do throughout the app. Admins have access to course management, student management, and the admin dashboard. Students have access to course browsing, enrollment, dropping courses, and viewing their history. Neither role has access to the other's features.

