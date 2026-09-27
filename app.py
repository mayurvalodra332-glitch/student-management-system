from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect("students.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            course TEXT NOT NULL,
            semester TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():

    search = request.args.get("search", "")
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row

    if search:
        students = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ?
            OR roll LIKE ?
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        students = conn.execute(
            "SELECT * FROM students"
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        students=students,
        search=search
    )


@app.route("/add_student", methods=["POST"])
def add_student():

    name = request.form.get("name")
    roll = request.form.get("roll")
    course = request.form.get("course")
    semester = request.form.get("semester")

    conn = sqlite3.connect("students.db")

    conn.execute("""
        INSERT INTO students
        (name, roll, course, semester)
        VALUES (?, ?, ?, ?)
    """, (name, roll, course, semester))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/delete_student/<int:id>")
def delete_student(id):

    conn = sqlite3.connect("students.db")

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


@app.route("/edit_student/<int:id>")
def edit_student(id):

    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_student.html",
        student=student
    )


@app.route("/update_student/<int:id>", methods=["POST"])
def update_student(id):

    name = request.form.get("name")
    roll = request.form.get("roll")
    course = request.form.get("course")
    semester = request.form.get("semester")

    conn = sqlite3.connect("students.db")

    conn.execute("""
        UPDATE students
        SET name = ?, roll = ?, course = ?, semester = ?
        WHERE id = ?
    """, (name, roll, course, semester, id))

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":

    init_db()

    app.run(debug=True)