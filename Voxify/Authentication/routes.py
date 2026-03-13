from flask import Blueprint, render_template, request, redirect, url_for, current_app

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

@auth_bp.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            role = user[5]

            if role == "admin":
                return redirect(url_for("admin.dashboard"))

            elif role == "voter":
                return redirect(url_for("voter.dashboard"))

    return render_template("login.html")

@auth_bp.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, password, role)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("auth.login"))

    return render_template("signup.html")