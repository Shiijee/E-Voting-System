from flask import Blueprint, render_template

voter_bp = Blueprint('voter', __name__)

@voter_bp.route("/dashboard")
def dashboard():
    return render_template("voter_dashboard.html")