from flask import Blueprint
from Voxify import mysql

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/dashboard")
def admin_dashboard():

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()

    return f"Admin Dashboard - {len(users)} users"