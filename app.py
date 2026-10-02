from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "student_management_secret_key_123"


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            course TEXT NOT NULL,
            semester TEXT NOT NULL
        )
    """)

    columns = conn.execute(
        "PRAGMA table_info(students)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "user_id" not in column_names:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN user_id INTEGER
        """)

    conn.commit()
    conn.close()


# =========================
# SIGN UP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template(
                "signup.html",
                error="Please fill all fields."
            )

        if len(password) < 6:
            return render_template(
                "signup.html",
                error="Password must be at least 6 characters."
            )

        if password != confirm_password:
            return render_template(
                "signup.html",
                error="Passwords do not match."
            )

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                hashed_password
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "signup.html",
                error="This email is already registered."
            )

    return render_template("signup.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =========================
# FORGOT PASSWORD
# =========================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user is None:
            return render_template(
                "forgot_password.html",
                error="No account found with this email."
            )

        return render_template(
            "reset_password.html",
            email=email
        )

    return render_template("forgot_password.html")


# =========================
# RESET PASSWORD
# =========================

@app.route("/reset_password", methods=["POST"])
def reset_password():

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if len(password) < 6:

        return render_template(
            "reset_password.html",
            email=email,
            error="Password must be at least 6 characters."
        )

    if password != confirm_password:

        return render_template(
            "reset_password.html",
            email=email,
            error="Passwords do not match."
        )

    hashed_password = generate_password_hash(password)

    conn = get_db()

    conn.execute("""
        UPDATE users
        SET password = ?
        WHERE email = ?
    """, (
        hashed_password,
        email
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "login",
            reset="success"
        )
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    user_id = session["user_id"]

    conn = get_db()

    if search:

        students = conn.execute("""
            SELECT * FROM students
            WHERE user_id = ?
            AND (
                name LIKE ?
                OR roll LIKE ?
            )
            ORDER BY id DESC
        """, (
            user_id,
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        students = conn.execute("""
            SELECT * FROM students
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    total_students = conn.execute("""
        SELECT COUNT(*)
        FROM students
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        students=students,
        search=search,
        total_students=total_students
    )


# =========================
# ADD STUDENT
# =========================

@app.route("/add_student", methods=["POST"])
def add_student():

    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    roll = request.form.get("roll", "").strip()
    course = request.form.get("course", "").strip()
    semester = request.form.get("semester", "").strip()

    conn = get_db()

    conn.execute("""
        INSERT INTO students
        (name, roll, course, semester, user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        roll,
        course,
        semester,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =========================
# DELETE STUDENT
# =========================

@app.route("/delete_student/<int:id>")
def delete_student(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM students
        WHERE id = ?
        AND user_id = ?
    """, (
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =========================
# EDIT STUDENT
# =========================

@app.route("/edit_student/<int:id>")
def edit_student(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    student = conn.execute("""
        SELECT * FROM students
        WHERE id = ?
        AND user_id = ?
    """, (
        id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if student is None:
        return redirect(url_for("home"))

    return render_template(
        "edit_student.html",
        student=student
    )


# =========================
# UPDATE STUDENT
# =========================

@app.route("/update_student/<int:id>", methods=["POST"])
def update_student(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    roll = request.form.get("roll", "").strip()
    course = request.form.get("course", "").strip()
    semester = request.form.get("semester", "").strip()

    conn = get_db()

    conn.execute("""
        UPDATE students
        SET name = ?,
            roll = ?,
            course = ?,
            semester = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        name,
        roll,
        course,
        semester,
        id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# =========================
# START
# =========================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)