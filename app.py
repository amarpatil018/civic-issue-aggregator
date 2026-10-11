from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Folder where uploaded images will be stored
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# DATABASE
# -----------------------------

def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


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


# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# REPORT PAGE
# -----------------------------

@app.route("/report")
def report():

    return render_template("report.html")


# -----------------------------
# SUBMIT REPORT
# -----------------------------

@app.route("/submit-report", methods=["POST"])
def submit_report():

    category = request.form.get("category")

    description = request.form.get("description")

    latitude = request.form.get("latitude")

    longitude = request.form.get("longitude")

    photo = request.files.get("photo")


    # -------------------------
    # AUTOMATIC DEPARTMENT
    # -------------------------

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


    # -------------------------
    # SAVE PHOTO
    # -------------------------

    photo_filename = None

    if photo and photo.filename:

        photo_filename = photo.filename

        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            photo_filename
        )

        photo.save(photo_path)


    # -------------------------
    # SAVE DATABASE
    # -------------------------

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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    connection.commit()

    issue_id = cursor.lastrowid

    connection.close()


    # -------------------------
    # SUCCESS PAGE
    # -------------------------

    return render_template(
        "success.html",
        issue_id=issue_id,
        category=category,
        department=department
    )


# -----------------------------
# START APPLICATION
# -----------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)