from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from Voxify.Authentication.routes import superadmin_required

superadmin_bp = Blueprint('super_admin', __name__,
                          template_folder='templates',
                          static_folder='static',
                          static_url_path='/superadmin/static')


@superadmin_bp.route("/")
@superadmin_bp.route("/dashboard")
@superadmin_required
def dashboard():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='admin'")
    total_admins = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter'")
    total_voters = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM elections")
    total_elections = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM votes")
    total_votes = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template('super_dashboard.html',
                           total_admins=total_admins,
                           total_voters=total_voters,
                           total_elections=total_elections,
                           total_votes=total_votes)


@superadmin_bp.route("/manage-admins")
@superadmin_required
def manage_admins():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, firstname, surname, username, created_at FROM users WHERE role='admin' ORDER BY created_at DESC")
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_admins.html', admins=admins)


@superadmin_bp.route("/create-admin", methods=["POST"])
@superadmin_required
def create_admin():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "admin").strip().lower()

    if not full_name or not username or not email or not password:
        flash("Full Name, Username, Email, and Password are required.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    name_parts = full_name.split()
    firstname = name_parts[0]
    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    hashed_password = generate_password_hash(password)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (firstname, surname, username, password, role, email, is_approved) VALUES (%s, %s, %s, %s, %s, %s, TRUE)",
            (firstname, surname, username, hashed_password, role, email)
        )
        conn.commit()
        flash("Admin account created successfully!", "success")
    except Exception as e:
        flash(f"Error creating admin: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('super_admin.manage_admins'))


@superadmin_bp.route("/delete-admin/<int:admin_id>")
@superadmin_required
def delete_admin(admin_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='admin'", (admin_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Admin deleted!", "success")
    return redirect(url_for('super_admin.manage_admins'))


@superadmin_bp.route("/system-logs")
@superadmin_required
def system_logs():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.*, u.firstname, u.surname, u.username
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 100
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('system_logs.html', logs=logs)
