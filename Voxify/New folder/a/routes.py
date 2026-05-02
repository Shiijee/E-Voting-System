from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import logging
from ..utils.otp import (
    generate_otp, send_otp_email, store_otp_in_session,
    verify_otp_from_session, clear_otp_from_session, is_otp_valid,
    set_trusted_device, check_trusted_device
)

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static', static_url_path='/auth/static')

logging.basicConfig(level=logging.DEBUG)

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
                flash("Your account is pending approval. Please wait for admin approval.", "warning")
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
# MAIN LOGIN ROUTES
# ============================================

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/voter-login", methods=["GET", "POST"])
def voter_login():
    """Main voter login page - Default entry point"""
    # If already logged in as voter, go to dashboard
    if 'user_id' in session:
        if session.get('role') == 'voter':
            return redirect(url_for('voter.dashboard'))
        elif session.get('role') in ['admin', 'superadmin']:
            return redirect(url_for('admin.dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        print(f"Login attempt - Student ID: {username}")  # Debug
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE student_id=%s AND role='voter'", 
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            print(f"User found: {user['student_id']}, Role: {user['role']}")  # Debug
            print(f"Stored password hash: {user['password'][:50]}...")  # Debug
            
            # Check password with error handling
            try:
                if check_password_hash(user['password'], password):
                    print("Password verified successfully!")
                    
                    if not user.get('is_approved', False):
                        flash("Your account is pending approval. Please contact the administrator.", "error")
                        return render_template("voter_login.html")

                    if not user.get('is_active', True):
                        flash("Your account has been archived. Please contact your college administrator.", "error")
                        return render_template("voter_login.html")
                    
                    # Check if device is trusted - skip OTP if trusted
                    if check_trusted_device(user['id']):
                        session.clear()
                        session['user_id'] = user['id']
                        session['role'] = user['role']
                        session['username'] = user['student_id']
                        session['fullname'] = f"{user['firstname']} {user['surname']}"
                        session.permanent = True
                        flash(f"Welcome, {user['firstname']}!", "success")
                        return redirect(url_for('voter.dashboard'))
                    
                    # Not trusted - send OTP
                    email = user.get('email')
                    if not email or '@' not in str(email):
                        flash("No valid email found for your account. Please contact the administrator.", "error")
                        return render_template("voter_login.html")

                    if session.get('user_data_voter_login', {}).get('user_id') == user['id'] and is_otp_valid('voter_login'):
                        flash("An OTP has already been sent. Please check your email and verify.", "info")
                        return redirect(url_for('auth.verify_otp', purpose='voter_login'))

                    clear_otp_from_session('voter_login')
                    otp = generate_otp()
                    store_otp_in_session(otp, 'voter_login', {
                        'user_id': user['id'], 'role': user['role'],
                        'username': user['student_id'],
                        'fullname': f"{user['firstname']} {user['surname']}",
                        'email': email
                    })
                    send_otp_email(email, otp)
                    fallback_otp = session.pop('_otp_fallback', None)
                    session.modified = True
                    if fallback_otp:
                        flash(f"Could not send OTP email. Your OTP is: {fallback_otp} (check server logs too)", "warning")
                    else:
                        flash("OTP sent to your email. Please verify to complete login.", "info")
                    return redirect(url_for('auth.verify_otp', purpose='voter_login'))
                else:
                    print("Password verification failed!")
            except ValueError as e:
                print(f"Password hash error: {e}")
                # If hash is invalid, try plain text comparison (temporary fix)
                if user['password'] == password:
                    print("Plain text password match! Updating hash...")
                    # Update to proper hash
                    new_hash = generate_password_hash(password)
                    conn = current_app.config["get_db_connection"]()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_hash, user['id']))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    session.clear()
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    session['username'] = user['student_id']
                    session['fullname'] = f"{user['firstname']} {user['surname']}"
                    session.permanent = True
                    
                    flash(f"Welcome, {user['firstname']}!", "success")
                    return redirect(url_for('voter.dashboard'))
        
        flash("Invalid Student ID or password.", "error")
    
    return render_template("voter_login.html")

@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Admin login page - Separate from voter login"""
    # If already logged in as admin, go to dashboard
    if 'user_id' in session:
        if session.get('role') in ['admin', 'superadmin']:
            if session.get('role') == 'superadmin':
                return redirect(url_for('super_admin.dashboard'))
            return redirect(url_for('admin.dashboard'))
        elif session.get('role') == 'voter':
            flash("Please use voter login page.", "info")
            return redirect(url_for('auth.voter_login'))
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE student_id=%s AND role IN ('admin', 'superadmin')", 
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            if not user.get('is_active', True):
                flash("Your account has been archived. Please contact the registrar.", "error")
                return render_template("admin_login.html")

            # Check if device is trusted - skip OTP if trusted
            if check_trusted_device(user['id']):
                session.clear()
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['username'] = user['student_id']
                session['fullname'] = f"{user['firstname']} {user['surname']}"
                session.permanent = True
                flash(f"Welcome back, {user['firstname']}!", "success")
                if user['role'] == 'superadmin':
                    return redirect(url_for('super_admin.dashboard'))
                else:
                    return redirect(url_for('admin.dashboard'))

            # Not trusted - send OTP
            email = user.get('email')
            if not email or '@' not in str(email):
                flash("No valid email found for your account. Please contact the administrator.", "error")
                return render_template("admin_login.html")

            if session.get('user_data_admin_login', {}).get('user_id') == user['id'] and is_otp_valid('admin_login'):
                flash("An OTP has already been sent. Please check your email and verify.", "info")
                return redirect(url_for('auth.verify_otp', purpose='admin_login'))

            clear_otp_from_session('admin_login')
            otp = generate_otp()
            store_otp_in_session(otp, 'admin_login', {
                'user_id': user['id'], 'role': user['role'],
                'username': user['student_id'],
                'fullname': f"{user['firstname']} {user['surname']}",
                'email': email
            })
            print(f"[DEBUG] Admin login OTP generation - user_id: {user['id']}, email: {email}, otp: {otp[:3]}***")
            send_otp_email(email, otp)
            fallback_otp = session.pop('_otp_fallback', None)
            session.modified = True
            if fallback_otp:
                flash(f"Could not send OTP email. Your OTP is: {fallback_otp} (check server logs too)", "warning")
                print(f"[DEBUG] OTP shown on screen for admin {user['id']}")
            else:
                flash("OTP sent to your email. Please verify to complete login.", "info")
                print(f"[DEBUG] OTP sent successfully for admin {user['id']}")
            return redirect(url_for('auth.verify_otp', purpose='admin_login'))
        
        flash("Invalid admin credentials.", "error")
    
    return render_template("admin_login.html")

# ============================================
# VOTER SIGNUP
# ============================================

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Signup disabled - admin creates voter accounts
    flash("Registration is closed. Please contact your college administrator.", "info")
    return redirect(url_for('auth.voter_login'))
    


@auth_bp.route("/logout")
def logout():
    if 'user_id' in session:
        log_activity(current_app.config["get_db_connection"], session['user_id'], "logout", "User logged out")
    
    session.clear()
    for key in list(session.keys()):
        session.pop(key, None)
    session.modified = True
    
    flash("You have been logged out successfully.", "success")
    
    response = make_response(redirect(url_for('auth.voter_login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.set_cookie('session', '', expires=0)
    response.set_cookie('evoting_session', '', expires=0)
    
    return response

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    purpose = request.args.get('purpose')
    if purpose not in ['signup', 'voter_login', 'admin_login']:
        flash("Invalid verification purpose.", "error")
        return redirect(url_for('auth.voter_login'))

    user_data_key = f'user_data_{purpose}'
    if user_data_key not in session:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.voter_login'))

    def render_verify_template():
        response = make_response(render_template("verify_otp.html", purpose=purpose, otp_expiry=otp_expiry))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    otp_key = f'otp_{purpose}'
    otp_expiry = None
    if otp_key in session:
        otp_expiry = session[otp_key].get('expiry')

    if request.method == "POST":
        otp = request.form.get('otp', '').strip()
        if not otp:
            flash("Please enter the OTP.", "error")
            return render_verify_template()

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
                        """INSERT INTO users (student_id, firstname, middlename, surname, username, password, role, email, college_id, is_approved)
                           VALUES (%s, %s, %s, %s, %s, %s, 'voter', %s, %s, FALSE)""",
                        (user_data['student_id'], user_data['firstname'], user_data['middlename'],
                         user_data['surname'], user_data['username'], user_data['password'],
                         user_data['email'], user_data.get('college_id'))
                    )
                    conn.commit()
                    session.pop(f'user_data_{purpose}', None)
                    flash("Registration successful! Please wait for admin approval.", "success")
                    return redirect(url_for("auth.voter_login"))
                except Exception as e:
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

    return render_verify_template()


@auth_bp.route("/resend-otp")
def resend_otp():
    purpose = request.args.get('purpose')
    if purpose not in ['signup', 'voter_login', 'admin_login']:
        flash("Invalid OTP resend request.", "error")
        return redirect(url_for('auth.voter_login'))

    user_data = session.get(f'user_data_{purpose}')
    if not user_data:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.voter_login'))

    email = user_data.get('email')
    if not email or '@' not in str(email):
        flash("No valid email found for your account. Please contact the administrator.", "error")
        return redirect(url_for('auth.verify_otp', purpose=purpose))

    otp = generate_otp()
    store_otp_in_session(otp, purpose, user_data)
    send_otp_email(email, otp)
    fallback_otp = session.pop('_otp_fallback', None)
    session.modified = True
    if fallback_otp:
        flash(f"Could not send OTP email. Your OTP is: {fallback_otp}", "warning")
    else:
        flash("A new OTP has been sent to your email. Please verify to continue.", "info")

    return redirect(url_for('auth.verify_otp', purpose=purpose))


# ============================================
# HELPER FUNCTIONS
# ============================================

def log_activity(get_db_connection, user_id, action, details):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO system_logs (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Logging error: {e}")

@auth_bp.route("/check-session")
def check_session():
    return {
        'session_exists': bool(session.get('user_id')),
        'session_data': dict(session),
        'user_id_in_session': 'user_id' in session,
        'role_in_session': 'role' in session
    }