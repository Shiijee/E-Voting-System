from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from ..utils.otp import (
    generate_otp, send_otp_email, store_otp_in_session,
    verify_otp_from_session, clear_otp_from_session,
    set_trusted_device, check_trusted_device
)

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static', static_url_path='/auth/static')


# ============================================
# DECORATORS
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            session.clear()
            session['next'] = request.url
            flash("Please log in to access that page.", "warning")
            return redirect(url_for('auth.voter_login'))
        try:
            conn = current_app.config["get_db_connection"]()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, role, is_approved FROM users WHERE id=%s", (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user:
                session.clear()
                flash("Your session has expired. Please log in again.", "warning")
                return redirect(url_for('auth.voter_login'))

            if user['role'] == 'voter' and not user.get('is_approved', False):
                session.clear()
                flash("Your account is pending approval.", "warning")
                return redirect(url_for('auth.voter_login'))

            if user['role'] != session.get('role'):
                session['role'] = user['role']
        except Exception as e:
            print(f"Session validation error: {e}")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'superadmin']:
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def voter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'voter':
            flash("Access denied. Voter privileges required.", "error")
            return redirect(url_for('auth.voter_login'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'superadmin':
            flash("Access denied. Super Admin privileges required.", "error")
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# VOTER LOGIN
# ============================================

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/voter-login", methods=["GET", "POST"])
def voter_login():
    if 'user_id' in session:
        if session.get('role') == 'voter':
            return redirect(url_for('voter.dashboard'))
        elif session.get('role') in ['admin', 'superadmin']:
            return redirect(url_for('admin.dashboard'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND role='voter'", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            if not user.get('is_approved', False):
                flash("Your account is pending approval. Please contact the administrator.", "error")
                return render_template("voter_login.html")

            if check_trusted_device(user['id']):
                session.clear()
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['username'] = user['username']
                session['fullname'] = f"{user['firstname']} {user['surname']}"
                session.permanent = True
                flash(f"Welcome, {user['firstname']}!", "success")
                return redirect(url_for('voter.dashboard'))

            email = user.get('email')
            if not email or '@' not in str(email):
                flash("No valid email found for your account. Please contact the administrator.", "error")
                return render_template("voter_login.html")

            otp = generate_otp()
            store_otp_in_session(otp, 'voter_login', {
                'user_id': user['id'], 'role': user['role'],
                'username': user['username'],
                'fullname': f"{user['firstname']} {user['surname']}"
            })
            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please verify to complete login.", "info")
                return redirect(url_for('auth.verify_otp', purpose='voter_login'))
            else:
                flash("Failed to send OTP. Please try again.", "error")
                return render_template("voter_login.html")

        flash("Invalid username or password.", "error")

    return render_template("voter_login.html")


# ============================================
# ADMIN LOGIN
# ============================================

@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if 'user_id' in session:
        if session.get('role') == 'superadmin':
            return redirect(url_for('super_admin.dashboard'))
        elif session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('role') == 'voter':
            flash("Please use voter login page.", "info")
            return redirect(url_for('auth.voter_login'))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND role IN ('admin', 'superadmin')", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            if check_trusted_device(user['id']):
                session.clear()
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['username'] = user['username']
                session['fullname'] = f"{user['firstname']} {user['surname']}"
                session.permanent = True
                flash(f"Welcome back, {user['firstname']}!", "success")
                if user['role'] == 'superadmin':
                    return redirect(url_for('super_admin.dashboard'))
                return redirect(url_for('admin.dashboard'))

            email = user.get('email')
            if not email or '@' not in str(email):
                flash("No valid email found for your account. Please contact the administrator.", "error")
                return render_template("admin_login.html")

            otp = generate_otp()
            store_otp_in_session(otp, 'admin_login', {
                'user_id': user['id'], 'role': user['role'],
                'username': user['username'],
                'fullname': f"{user['firstname']} {user['surname']}"
            })
            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please verify to complete login.", "info")
                return redirect(url_for('auth.verify_otp', purpose='admin_login'))
            else:
                flash("Failed to send OTP. Please try again.", "error")
                return render_template("admin_login.html")

        flash("Invalid admin credentials.", "error")

    return render_template("admin_login.html")


# ============================================
# VOTER SIGNUP
# ============================================

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if 'user_id' in session:
        return redirect(url_for('auth.voter_login'))

    if request.method == "POST":
        surname = request.form["surname"]
        firstname = request.form["firstname"]
        middlename = request.form.get("middlename", "")
        email = request.form["email"]
        student_id = request.form["student_id"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("signup.html")

        hashed_password = generate_password_hash(password)

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=%s OR student_id=%s", (username, student_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Username or Student ID already exists", "error")
            return render_template("signup.html")
        cursor.close()
        conn.close()

        otp = generate_otp()
        store_otp_in_session(otp, 'signup', {
            'student_id': student_id, 'firstname': firstname,
            'middlename': middlename, 'surname': surname,
            'username': username, 'password': hashed_password,
            'email': email
        })
        if send_otp_email(email, otp):
            flash("OTP sent to your email. Please verify to complete registration.", "info")
            return redirect(url_for('auth.verify_otp', purpose='signup'))
        else:
            flash("Failed to send OTP. Please try again.", "error")
            return render_template("signup.html")

    return render_template("signup.html")


# ============================================
# OTP VERIFICATION
# ============================================

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    purpose = request.args.get('purpose')
    if purpose not in ['signup', 'voter_login', 'admin_login']:
        flash("Invalid verification purpose.", "error")
        return redirect(url_for('auth.voter_login'))

    if request.method == "POST":
        otp = request.form.get('otp', '').strip()
        if not otp:
            flash("Please enter the OTP.", "error")
            return render_template("verify_otp.html", purpose=purpose)

        success, message = verify_otp_from_session(otp, purpose)

        if success:
            if purpose == 'signup':
                user_data = session.get(f'user_data_{purpose}')
                if not user_data:
                    flash("Session expired. Please sign up again.", "error")
                    return redirect(url_for('auth.signup'))
                conn = current_app.config["get_db_connection"]()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """INSERT INTO users (student_id, firstname, middlename, surname, username, password, role, email, is_approved)
                           VALUES (%s, %s, %s, %s, %s, %s, 'voter', %s, FALSE)""",
                        (user_data['student_id'], user_data['firstname'], user_data['middlename'],
                         user_data['surname'], user_data['username'], user_data['password'], user_data['email'])
                    )
                    conn.commit()
                    session.pop(f'user_data_{purpose}', None)
                    flash("Registration successful! Please wait for admin approval.", "success")
                    return redirect(url_for("auth.voter_login"))
                except Exception:
                    conn.rollback()
                    flash("Error creating account. Please try again.", "error")
                    return redirect(url_for('auth.signup'))
                finally:
                    cursor.close()
                    conn.close()

            elif purpose in ['voter_login', 'admin_login']:
                user_data = session.get(f'user_data_{purpose}')
                if not user_data:
                    flash("Session expired. Please log in again.", "error")
                    return redirect(url_for('auth.voter_login'))
                session.clear()
                session['user_id'] = user_data['user_id']
                session['role'] = user_data['role']
                session['username'] = user_data['username']
                session['fullname'] = user_data['fullname']
                session['login_time'] = datetime.now().isoformat()
                session.permanent = True

                response = make_response()
                set_trusted_device(user_data['user_id'], response)

                role = user_data['role']
                if role == 'superadmin':
                    response.headers['Location'] = url_for('super_admin.dashboard')
                elif role == 'admin':
                    response.headers['Location'] = url_for('admin.dashboard')
                else:
                    response.headers['Location'] = url_for('voter.dashboard')
                response.status_code = 302
                return response
        else:
            flash(message, "error")

    return render_template("verify_otp.html", purpose=purpose)


# ============================================
# LOGOUT
# ============================================

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    response = make_response(redirect(url_for('auth.voter_login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.set_cookie('evoting_session', '', expires=0)
    return response
