from flask import Blueprint
from Voxify import mysql

voter_bp = Blueprint('voter', __name__)

@voter_bp.route("/dashboard")
def voter_dashboard():

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    cursor.close()

    return f"Voter Dashboard - {len(candidates)} candidates"