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
    cursor.execute("SELECT id, firstname, surname, student_id, email, role, created_at, is_active FROM users WHERE role='admin' ORDER BY created_at DESC")
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_admins.html', admins=admins)


@superadmin_bp.route("/manage-colleges")
@superadmin_required
def manage_colleges():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT c.id, c.name, c.created_at,
               (SELECT COUNT(*) FROM users u WHERE u.college_id=c.id AND u.role='admin') AS admin_count,
               (SELECT COUNT(*) FROM users u WHERE u.college_id=c.id AND u.role='voter') AS voter_count,
               (SELECT COUNT(*) FROM elections e WHERE e.college_id=c.id) AS election_count
        FROM colleges c
        ORDER BY c.created_at DESC
        """
    )
    colleges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_colleges.html', colleges=colleges)


@superadmin_bp.route("/create-college", methods=["POST"])
@superadmin_required
def create_college():
    name = request.form.get("name", "").strip()
    if not name:
        flash("College name is required.", "error")
        return redirect(url_for('super_admin.manage_colleges'))

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO colleges (name) VALUES (%s)", (name,))
        conn.commit()
        flash("College created successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error creating college: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('super_admin.manage_colleges'))


@superadmin_bp.route("/edit-college/<int:college_id>", methods=["POST"])
@superadmin_required
def edit_college(college_id):
    name = request.form.get("name", "").strip()
    if not name:
        flash("College name is required.", "error")
        return redirect(url_for('super_admin.manage_colleges'))

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE colleges SET name=%s WHERE id=%s", (name, college_id))
        conn.commit()
        if cursor.rowcount == 0:
            flash("College not found.", "error")
        else:
            flash("College updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error updating college: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('super_admin.manage_colleges'))


@superadmin_bp.route("/delete-college/<int:college_id>")
@superadmin_required
def delete_college(college_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM colleges WHERE id=%s", (college_id,))
        conn.commit()
        if cursor.rowcount == 0:
            flash("College not found.", "error")
        else:
            flash("College deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting college: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('super_admin.manage_colleges'))


@superadmin_bp.route("/create-admin", methods=["POST"])
@superadmin_required
def create_admin():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "admin").strip().lower()

    if not full_name or not email or not password:
        flash("Full Name, Email, and Password are required.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    name_parts = full_name.split()
    firstname = name_parts[0]
    surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    hashed_password = generate_password_hash(password)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        # Auto-generate student_id: admin-0001, admin-0002, ...
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role IN ('admin','superadmin')")
        row = cursor.fetchone()
        count = row['cnt'] if isinstance(row, dict) else row[0]
        new_student_id = f"admin-{str(count + 1).zfill(4)}"

        cursor.execute(
            "INSERT INTO users (firstname, surname, student_id, password, role, email, is_approved) VALUES (%s, %s, %s, %s, %s, %s, TRUE)",
            (firstname, surname, new_student_id, hashed_password, role, email)
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

@superadmin_bp.route("/edit-admin/<int:admin_id>", methods=["GET", "POST"])
@superadmin_required
def edit_admin(admin_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s AND role='admin'", (admin_id,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if not admin:
        flash("Admin not found.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    if request.method == "POST":
        firstname = request.form["firstname"]
        surname = request.form["surname"]
        email = request.form["email"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET firstname=%s, surname=%s, email=%s WHERE id=%s AND role='admin'",
                (firstname, surname, email, admin_id)
            )
            conn.commit()
            flash("Admin updated successfully!", "success")
            return redirect(url_for('super_admin.manage_admins'))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating admin: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('admin_form.html', action='edit', admin=admin)

@superadmin_bp.route("/archive-admin/<int:admin_id>")
@superadmin_required
def archive_admin(admin_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active=FALSE WHERE id=%s AND role='admin'", (admin_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Admin archived!", "warning")
    return redirect(url_for('super_admin.manage_admins'))


@superadmin_bp.route("/system-logs")
@superadmin_required
def system_logs():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.*, u.firstname, u.surname, u.student_id
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 100
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('system_logs.html', logs=logs)