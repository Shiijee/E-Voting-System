from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]
            session['role'] = user[5]
            role = user[5]

            if role == "admin":
                return redirect(url_for("admin.dashboard"))

            elif role == "voter":
                return redirect(url_for("voter.dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Username already exists", "error")
            return render_template("signup.html")

        cursor.execute(
            "INSERT INTO users (name, username, password, role) VALUES (%s, %s, %s, %s)",
            (name, username, password, role)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")
