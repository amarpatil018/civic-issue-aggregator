from flask import Flask, render_template, request
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================
# UPLOAD FOLDER
# ==========================================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():

    connection = sqlite3.connect("database.db")

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS issues (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category TEXT NOT NULL,

            description TEXT NOT NULL,

            photo TEXT,

            latitude REAL,

            longitude REAL,

            status TEXT DEFAULT 'Pending',

            department TEXT,

            created_at TEXT NOT NULL

        )
    """)

    connection.commit()

    connection.close()

    print("Database created successfully!")


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# REPORT PAGE
# ==========================================

@app.route("/report")
def report():

    return render_template("report.html")


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
def admin():

    connection = get_db_connection()

    # Get all complaints
    issues = connection.execute(
        "SELECT * FROM issues ORDER BY id DESC"
    ).fetchall()

    # Total complaints
    total = connection.execute(
        "SELECT COUNT(*) FROM issues"
    ).fetchone()[0]

    # Pending complaints
    pending = connection.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'Pending'"
    ).fetchone()[0]

    # In Progress complaints
    in_progress = connection.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'In Progress'"
    ).fetchone()[0]

    # Resolved complaints
    resolved = connection.execute(
        "SELECT COUNT(*) FROM issues WHERE status = 'Resolved'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "admin.html",
        issues=issues,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )


# ==========================================
# SUBMIT COMPLAINT
# ==========================================

@app.route("/submit-report", methods=["POST"])
def submit_report():

    # Get form data
    category = request.form.get("category")

    description = request.form.get("description")

    latitude = request.form.get("latitude")

    longitude = request.form.get("longitude")

    photo = request.files.get("photo")


    # ==========================================
    # DEPARTMENT ASSIGNMENT
    # ==========================================

    department_mapping = {

        "Pothole": "Road Department",

        "Damaged Road": "Road Department",

        "Streetlight": "Electrical Department",

        "Garbage": "Sanitation Department",

        "Water Leakage": "Water Department",

        "Waterlogging": "Drainage Department"

    }


    department = department_mapping.get(

        category,

        "Municipal Department"

    )


    # ==========================================
    # SAVE PHOTO
    # ==========================================

    photo_filename = None


    if photo and photo.filename:

        photo_filename = photo.filename

        photo_path = os.path.join(

            app.config["UPLOAD_FOLDER"],

            photo_filename

        )

        photo.save(photo_path)


    # ==========================================
    # SAVE COMPLAINT TO DATABASE
    # ==========================================

    connection = get_db_connection()


    cursor = connection.execute(

        """
        INSERT INTO issues
        (
            category,
            description,
            photo,
            latitude,
            longitude,
            status,
            department,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (

            category,

            description,

            photo_filename,

            latitude,

            longitude,

            "Pending",

            department,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        )

    )


    connection.commit()


    # Get generated complaint ID
    issue_id = cursor.lastrowid


    connection.close()


    # ==========================================
    # SUCCESS PAGE
    # ==========================================

    return render_template(

        "success.html",

        issue_id=issue_id,

        category=category,

        department=department

    )


# ==========================================
# START FLASK APPLICATION
# ==========================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)