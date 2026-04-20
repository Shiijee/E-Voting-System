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

    cursor.execute("SELECT COUNT(*) as total FROM colleges")
    total_colleges = cursor.fetchone()['total']

    cursor.execute("""
        SELECT u.id, u.firstname, u.surname, u.email, u.student_id, u.created_at, u.is_active,
               c.name as college_name
        FROM users u LEFT JOIN colleges c ON u.college_id = c.id
        WHERE u.role='admin' ORDER BY u.created_at DESC LIMIT 5
    """)
    recent_admins = cursor.fetchall()

    cursor.execute("""
        SELECT l.id, l.action, l.created_at, u.firstname, u.surname, u.role
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC LIMIT 10
    """)
    recent_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('super_dashboard.html',
                           total_admins=total_admins,
                           total_colleges=total_colleges,
                           recent_admins=recent_admins,
                           recent_logs=recent_logs)


@superadmin_bp.route("/manage-admins")
@superadmin_required
def manage_admins():
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    college_filter = request.args.get('college_filter', '').strip()
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='admin'")
    total_admins = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='admin' AND is_active=TRUE AND COALESCE(is_archived, FALSE)=FALSE")
    active_admins = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='admin' AND is_active=FALSE AND COALESCE(is_archived, FALSE)=FALSE")
    inactive_admins = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='admin' AND COALESCE(is_archived, FALSE)=TRUE")
    archived_admins = cursor.fetchone()['total']
    status_counts = {
        'all': total_admins,
        'active': active_admins,
        'inactive': inactive_admins,
        'archived': archived_admins
    }
    
    query = "SELECT u.id, u.firstname, u.surname, u.student_id, u.email, u.role, u.created_at, u.is_active, COALESCE(u.is_archived, FALSE) AS is_archived, c.name as college_name FROM users u LEFT JOIN colleges c ON u.college_id = c.id WHERE u.role='admin'"
    params = []
    
    if status == 'active':
        query += " AND u.is_active=TRUE AND COALESCE(u.is_archived, FALSE)=FALSE"
    elif status == 'inactive':
        query += " AND u.is_active=FALSE AND COALESCE(u.is_archived, FALSE)=FALSE"
    elif status == 'archived':
        query += " AND COALESCE(u.is_archived, FALSE)=TRUE"
    
    if college_filter:
        query += " AND u.college_id=%s"
        params.append(college_filter)
    
    if search:
        query += " AND (u.firstname LIKE %s OR u.surname LIKE %s OR u.student_id LIKE %s OR u.email LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])
    
    query += " ORDER BY u.created_at DESC"
    
    cursor.execute(query, params)
    admins = cursor.fetchall()
    
    # Fetch colleges for the dropdown
    cursor.execute("SELECT id, name FROM colleges ORDER BY name")
    colleges = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('manage_admins.html', admins=admins, status=status, search=search, college_filter=college_filter, colleges=colleges, status_counts=status_counts)


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
    firstname = request.form.get("firstname", "").strip()
    middlename = request.form.get("middlename", "").strip()
    surname = request.form.get("surname", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    college_id = request.form.get("college_id", "").strip()
    role = "admin"  # Only admin role is allowed

    if not firstname or not surname or not email or not password or not confirm_password or not college_id:
        flash("All fields except middle name are required.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('super_admin.manage_admins'))

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
            "INSERT INTO users (firstname, middlename, surname, student_id, password, role, email, college_id, is_approved) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)",
            (firstname, middlename, surname, new_student_id, hashed_password, role, email, college_id)
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
    status = request.args.get('status', 'all')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='admin'", (admin_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Admin deleted!", "success")
    return redirect(url_for('super_admin.manage_admins', status=status if status != 'all' else None))

@superadmin_bp.route("/edit-admin/<int:admin_id>", methods=["GET", "POST"])
@superadmin_required
def edit_admin(admin_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s AND role='admin'", (admin_id,))
    admin = cursor.fetchone()
    
    # Fetch colleges for the dropdown
    cursor.execute("SELECT id, name FROM colleges ORDER BY name")
    colleges = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not admin:
        flash("Admin not found.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        college_id = request.form.get("college_id", "").strip()
        password = request.form.get("password", "").strip()

        if not full_name or not email or not college_id:
            flash("Full Name, Email, and College are required.", "error")
            return redirect(request.url)

        name_parts = full_name.split()
        firstname = name_parts[0]
        surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        try:
            if password:
                from werkzeug.security import generate_password_hash
                cursor.execute(
                    "UPDATE users SET firstname=%s, surname=%s, email=%s, college_id=%s, password=%s WHERE id=%s AND role='admin'",
                    (firstname, surname, email, college_id, generate_password_hash(password), admin_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET firstname=%s, surname=%s, email=%s, college_id=%s WHERE id=%s AND role='admin'",
                    (firstname, surname, email, college_id, admin_id)
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

    return render_template('admin_form.html', action='edit', admin=admin, colleges=colleges)

@superadmin_bp.route("/archive-admin/<int:admin_id>")
@superadmin_required
def archive_admin(admin_id):
    status = request.args.get('status', 'all')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_active, COALESCE(is_archived, FALSE) AS is_archived FROM users WHERE id=%s AND role='admin'", (admin_id,))
    admin = cursor.fetchone()
    if admin:
        if admin['is_archived']:
            cursor.execute("UPDATE users SET is_active=TRUE, is_archived=FALSE WHERE id=%s AND role='admin'", (admin_id,))
            conn.commit()
            flash("Admin restored!", "success")
        else:
            cursor.execute("UPDATE users SET is_active=FALSE, is_archived=TRUE WHERE id=%s AND role='admin'", (admin_id,))
            conn.commit()
            flash("Admin archived!", "warning")
    cursor.close()
    conn.close()
    return redirect(url_for('super_admin.manage_admins', status=status if status != 'all' else None))


@superadmin_bp.route("/toggle-admin-status/<int:admin_id>")
@superadmin_required
def toggle_admin_status(admin_id):
    action = request.args.get('action', 'toggle')
    status = request.args.get('status', 'all')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_active FROM users WHERE id=%s AND role='admin'", (admin_id,))
    admin = cursor.fetchone()
    if admin:
        if action == 'activate':
            new_status = True
            archive_status = False
            flash_text = "Admin restored!"
            flash_category = "success"
        elif action == 'deactivate':
            new_status = False
            archive_status = False
            flash_text = "Admin deactivated!"
            flash_category = "warning"
        else:
            new_status = not admin['is_active']
            archive_status = False
            flash_text = "Admin restored!" if new_status else "Admin deactivated!"
            flash_category = "success" if new_status else "warning"
        cursor.execute("UPDATE users SET is_active=%s, is_archived=%s WHERE id=%s AND role='admin'", (new_status, archive_status, admin_id))
        conn.commit()
        flash(flash_text, flash_category)
    cursor.close()
    conn.close()
    if action == 'deactivate':
        redirect_status = 'inactive'
    elif action == 'activate':
        redirect_status = 'active'
    else:
        redirect_status = status if status != 'all' else None
    return redirect(url_for('super_admin.manage_admins', status=redirect_status))


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