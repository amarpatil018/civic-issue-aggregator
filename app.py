
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify
)

import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__)

# -----------------------------------
# PROJECT CONFIGURATION
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "static", "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_STATUSES = [
    "Pending",
    "In Progress",
    "Resolved"
]

VALID_CATEGORIES = [
    "Pothole",
    "Streetlight",
    "Garbage",
    "Water Leakage",
    "Damaged Road",
    "Waterlogging"
]

# Kalaburagi city center
CITY_LATITUDE = 17.3297
CITY_LONGITUDE = 76.8343


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# -----------------------------------
# CREATE DATABASE
# -----------------------------------

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


# -----------------------------------
# DEPARTMENT ASSIGNMENT
# -----------------------------------

def get_department(category):

    department_mapping = {

        "Pothole": "Road Department",

        "Damaged Road": "Road Department",

        "Streetlight": "Electrical Department",

        "Garbage": "Sanitation Department",

        "Water Leakage": "Water Department",

        "Waterlogging": "Drainage Department"

    }

    return department_mapping.get(
        category,
        "General Department"
    )


# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------------
# REPORT PAGE
# -----------------------------------

@app.route("/report")
def report():

    return render_template("report.html")


# -----------------------------------
# SUBMIT COMPLAINT
# -----------------------------------

@app.route("/submit-report", methods=["POST"])
def submit_report():

    category = request.form.get(
        "category", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    latitude = request.form.get("latitude") or None

    longitude = request.form.get("longitude") or None

    photo = request.files.get("photo")

    # Validate category
    if category not in VALID_CATEGORIES:

        return "Please select a valid issue category.", 400

    # Validate description
    if not description:

        return "Please enter a description.", 400

    # Validate GPS coordinates if supplied
    try:

        if latitude is not None:

            latitude = float(latitude)

            if not -90 <= latitude <= 90:
                return "Invalid latitude.", 400

        if longitude is not None:

            longitude = float(longitude)

            if not -180 <= longitude <= 180:
                return "Invalid longitude.", 400

    except ValueError:

        return "Invalid GPS coordinates.", 400

    department = get_department(category)

    photo_filename = None

    # Save uploaded photo
    if photo and photo.filename:

        safe_filename = secure_filename(photo.filename)

        if not safe_filename:

            return "Please choose a valid photo filename.", 400

        unique_filename = (
            datetime.now().strftime("%Y%m%d%H%M%S%f")
            + "_"
            + safe_filename
        )

        photo_path = os.path.join(
            UPLOAD_FOLDER,
            unique_filename
        )

        photo.save(photo_path)

        photo_filename = unique_filename

    # Save complaint in database
    connection = get_db_connection()

    cursor = connection.execute("""

        INSERT INTO issues (

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

    """, (

        category,
        description,
        photo_filename,
        latitude,
        longitude,
        "Pending",
        department,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ))

    connection.commit()

    issue_id = cursor.lastrowid

    connection.close()

    return render_template(

        "success.html",

        issue_id=issue_id,

        category=category,

        department=department

    )


# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------

@app.route("/admin")
def admin():

    connection = get_db_connection()

    issues = connection.execute("""

        SELECT *
        FROM issues
        ORDER BY id DESC

    """).fetchall()

    total = connection.execute("""

        SELECT COUNT(*)
        FROM issues

    """).fetchone()[0]

    pending = connection.execute("""

        SELECT COUNT(*)
        FROM issues
        WHERE status = 'Pending'

    """).fetchone()[0]

    in_progress = connection.execute("""

        SELECT COUNT(*)
        FROM issues
        WHERE status = 'In Progress'

    """).fetchone()[0]

    resolved = connection.execute("""

        SELECT COUNT(*)
        FROM issues
        WHERE status = 'Resolved'

    """).fetchone()[0]

    connection.close()

    return render_template(

        "admin.html",

        issues=issues,

        total=total,

        pending=pending,

        in_progress=in_progress,

        resolved=resolved,

        city_latitude=CITY_LATITUDE,

        city_longitude=CITY_LONGITUDE

    )


# -----------------------------------
# UPDATE COMPLAINT STATUS
# -----------------------------------

@app.route(
    "/update-status/<int:issue_id>",
    methods=["POST"]
)

def update_status(issue_id):

    new_status = request.form.get("status", "")

    if new_status not in ALLOWED_STATUSES:

        return "Invalid complaint status.", 400

    connection = get_db_connection()

    existing_issue = connection.execute("""

        SELECT id
        FROM issues
        WHERE id = ?

    """, (issue_id,)).fetchone()

    if existing_issue is None:

        connection.close()

        return "Complaint not found.", 404

    connection.execute("""

        UPDATE issues

        SET status = ?

        WHERE id = ?

    """, (new_status, issue_id))

    connection.commit()

    connection.close()

    return redirect(url_for("admin"))


# -----------------------------------
# LIVE MAP API
# -----------------------------------

@app.route("/api/issues")
def get_issues():

    connection = get_db_connection()

    issues = connection.execute("""

        SELECT

            id,
            category,
            description,
            photo,
            latitude,
            longitude,
            status,
            department,
            created_at

        FROM issues

        WHERE latitude IS NOT NULL
        AND longitude IS NOT NULL
        AND latitude != ''
        AND longitude != ''

        ORDER BY id DESC

    """).fetchall()

    connection.close()

    return jsonify([dict(issue) for issue in issues])


# -----------------------------------
# RUN APPLICATION
# -----------------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)
