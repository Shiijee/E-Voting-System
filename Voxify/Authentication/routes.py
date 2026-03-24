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

        if user and check_password_hash(user[6], password):
            session['user_id'] = user[0]
            session['role'] = user[7]
            role = user[7]

            if role == "admin":
                return redirect(url_for("admin.dashboard"))

            elif role == "voter":
                return redirect(url_for("voter.dashboard"))

            elif role == "superadmin":
                return redirect(url_for("super_admin.dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        surname = request.form["surname"]
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        email = request.form["email"]
        username = request.form["student_id"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")

        password = generate_password_hash(password)

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Username already exists", "error")
            return render_template("signup.html")

        # For now, set role to 'voter', student_id to email (assuming email as student_id)
        role = 'voter'
        student_id = email

        cursor.execute(
            "INSERT INTO users (student_id, firstname, middlename, surname, username, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (student_id, firstname, middlename, surname, username, password, role)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")
