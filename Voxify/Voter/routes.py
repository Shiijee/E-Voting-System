from flask import Blueprint, render_template, session, redirect, url_for

voter_bp = Blueprint('voter', __name__, template_folder='templates')

@voter_bp.route("/dashboard")
def dashboard():
    if 'user_id' not in session or session.get('role') != 'voter':
        return redirect(url_for('auth.login'))
    return render_template("voter_dashboard.html")
