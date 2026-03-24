from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static')

# Setup logging
logging.basicConfig(level=logging.DEBUG)


# ─────────────────────────────────────────────
# Decorator: require a valid session
# ─────────────────────────────────────────────
def login_required(f):
    """Redirect to login if no valid session exists.
    Saves the requested URL so the user is returned there after login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            # Clear any partial session data
            session.clear()
            # Remember where the user was trying to go
            session['next'] = request.url
            flash("Please log in to access that page.", "warning")
            return redirect(url_for('auth.login'))
        
        # Verify user still exists in database
        try:
            conn = current_app.config["get_db_connection"]()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, role FROM users WHERE id=%s", (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user:
                session.clear()
                flash("Your session has expired. Please log in again.", "warning")
                return redirect(url_for('auth.login'))
            
            # Update session role if changed in database
            if user['role'] != session.get('role'):
                session['role'] = user['role']
                
        except Exception as e:
            print(f"Session validation error: {e}")
            
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# Role-specific decorators (optional helpers)
# ─────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            session['next'] = request.url
            flash("Please log in to access that page.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def voter_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            session['next'] = request.url
            flash("Please log in to access that page.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'voter':
            flash("Access denied. Voter privileges required.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            session['next'] = request.url
            flash("Please log in to access that page.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'superadmin':
            flash("Access denied. Super Admin privileges required.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    print(f"Login route - Session before: {dict(session)}")  # Debug
    
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session and 'role' in session:
        role = session.get('role')
        print(f"User already logged in as {role}")  # Debug
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'voter':
            return redirect(url_for('voter.dashboard'))
        elif role == 'superadmin':
            return redirect(url_for('super_admin.dashboard'))
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        print(f"Attempting login for: {username}")  # Debug

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            print(f"Login successful for: {username}")  # Debug
            
            # Clear any existing session data
            session.clear()
            
            # Set new session data
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            session['login_time'] = datetime.now().isoformat()
            
            # Make session permanent
            session.permanent = True
            
            print(f"Session after login: {dict(session)}")  # Debug
            
            role = user['role']

            # Redirect to the originally requested URL (if any), else role dashboard
            next_url = session.pop('next', None)

            if next_url:
                return redirect(next_url)

            if role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif role == "voter":
                return redirect(url_for("voter.dashboard"))
            elif role == "superadmin":
                return redirect(url_for("super_admin.dashboard"))

        flash("Invalid username or password", "error")

    # Add cache control headers to prevent back button issues
    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    print("=" * 50)
    print("LOGOUT ROUTE CALLED")
    print(f"Session before clear: {dict(session)}")
    print("=" * 50)
    
    # Method 1: Clear session dictionary
    session.clear()
    
    # Method 2: Pop all keys
    for key in list(session.keys()):
        session.pop(key, None)
    
    # Method 3: Set modified flag
    session.modified = True
    
    # Method 4: Expire the session cookie
    session.permanent = False
    
    print(f"Session after clear: {dict(session)}")
    print("Logout complete")
    print("=" * 50)
    
    flash("You have been logged out successfully.", "success")
    
    # Create response with multiple cache control headers
    response = make_response(redirect(url_for('auth.login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Expire all possible session cookies
    response.set_cookie('session', '', expires=0, max_age=0)
    response.set_cookie('evoting_session', '', expires=0, max_age=0)
    response.set_cookie('cookie', '', expires=0, max_age=0)
    
    return response


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Redirect logged-in users away from signup
    if 'user_id' in session:
        return redirect(url_for('auth.login'))

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

        hashed_password = generate_password_hash(password)

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Username already exists", "error")
            return render_template("signup.html")

        role = 'voter'
        student_id = email

        cursor.execute(
            "INSERT INTO users (student_id, firstname, middlename, surname, username, password, role) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (student_id, firstname, middlename, surname, username, hashed_password, role)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    # Add cache control headers
    response = make_response(render_template("signup.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# Debug route to check session status
@auth_bp.route("/check-session")
def check_session():
    """Debug route to check current session data"""
    session_data = dict(session)
    return {
        'session_exists': bool(session_data),
        'session_data': session_data,
        'user_id_in_session': 'user_id' in session,
        'role_in_session': 'role' in session
    }