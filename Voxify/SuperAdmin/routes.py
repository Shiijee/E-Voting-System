from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.security import generate_password_hash
from Voxify.Authentication.routes import superadmin_required
from Voxify.utils.otp import send_account_email

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
        WHERE u.role IN ('admin', 'superadmin')
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
    page = max(1, int(request.args.get('page', 1) or 1))
    per_page = 10

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

    base_query = "SELECT u.id, u.firstname, u.surname, u.student_id, u.email, u.role, u.created_at, u.is_active, COALESCE(u.is_archived, FALSE) AS is_archived, c.name as college_name FROM users u LEFT JOIN colleges c ON u.college_id = c.id WHERE u.role='admin'"
    count_query = "SELECT COUNT(*) as total FROM users u LEFT JOIN colleges c ON u.college_id = c.id WHERE u.role='admin'"
    params = []

    if status == 'active':
        base_query += " AND u.is_active=TRUE AND COALESCE(u.is_archived, FALSE)=FALSE"
        count_query += " AND u.is_active=TRUE AND COALESCE(u.is_archived, FALSE)=FALSE"
    elif status == 'inactive':
        base_query += " AND u.is_active=FALSE AND COALESCE(u.is_archived, FALSE)=FALSE"
        count_query += " AND u.is_active=FALSE AND COALESCE(u.is_archived, FALSE)=FALSE"
    elif status == 'archived':
        base_query += " AND COALESCE(u.is_archived, FALSE)=TRUE"
        count_query += " AND COALESCE(u.is_archived, FALSE)=TRUE"

    if college_filter:
        base_query += " AND u.college_id=%s"
        count_query += " AND u.college_id=%s"
        params.append(college_filter)

    if search:
        base_query += " AND (u.firstname LIKE %s OR u.surname LIKE %s OR u.student_id LIKE %s OR u.email LIKE %s)"
        count_query += " AND (u.firstname LIKE %s OR u.surname LIKE %s OR u.student_id LIKE %s OR u.email LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    cursor.execute(count_query, params)
    total_filtered = cursor.fetchone()['total']
    total_pages = max(1, (total_filtered + per_page - 1) // per_page)
    page = min(page, total_pages)

    base_query += " ORDER BY u.created_at DESC LIMIT %s OFFSET %s"
    cursor.execute(base_query, params + [per_page, (page - 1) * per_page])
    admins = cursor.fetchall()

    cursor.execute("SELECT id, name FROM colleges ORDER BY name")
    colleges = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('manage_admins.html', admins=admins, status=status, search=search,
                           college_filter=college_filter, colleges=colleges, status_counts=status_counts,
                           page=page, total_pages=total_pages, total_filtered=total_filtered, per_page=per_page)


@superadmin_bp.route("/manage-colleges")
@superadmin_required
def manage_colleges():
    page = max(1, int(request.args.get('page', 1) or 1))
    per_page = 10

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM colleges")
    total_colleges = cursor.fetchone()['total']
    total_pages = max(1, (total_colleges + per_page - 1) // per_page)
    page = min(page, total_pages)

    cursor.execute(
        """
        SELECT c.id, c.name, c.created_at,
               (SELECT COUNT(*) FROM users u WHERE u.college_id=c.id AND u.role='admin') AS admin_count,
               (SELECT COUNT(*) FROM users u WHERE u.college_id=c.id AND u.role='voter') AS voter_count,
               (SELECT COUNT(*) FROM elections e WHERE e.college_id=c.id) AS election_count
        FROM colleges c
        ORDER BY c.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (per_page, (page - 1) * per_page)
    )
    colleges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_colleges.html', colleges=colleges,
                           page=page, total_pages=total_pages, total_colleges=total_colleges, per_page=per_page)


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
    role = "admin"                              

    if not firstname or not surname or not email or not password or not confirm_password or not college_id:
        flash("All fields except middle name are required.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('super_admin.manage_admins'))

    hashed_password = generate_password_hash(password)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
                                                               
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role IN ('admin','superadmin')")
        row = cursor.fetchone()
        count = row['cnt'] if isinstance(row, dict) else row[0]
        new_student_id = f"admin-{str(count + 1).zfill(4)}"

        cursor.execute(
            "INSERT INTO users (firstname, middlename, surname, student_id, password, role, email, college_id, is_approved, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)",
            (firstname, middlename, surname, new_student_id, hashed_password, role, email, college_id)
        )
        conn.commit()
        email_sent = False
        if email and '@' in email:
            email_sent = send_account_email(
                email, 'admin', new_student_id, password,
                fullname=f"{firstname} {surname}",
                extra_info=f"College ID: {college_id}"
            )
        message = "Admin account created successfully!"
        if email_sent:
            message += " Email notification sent."
        else:
            message += " Could not send notification email."
        flash(message, "success")
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
    cursor.execute("SELECT is_active, COALESCE(is_archived, FALSE) AS is_archived, college_id FROM users WHERE id=%s AND role='admin'", (admin_id,))
    admin = cursor.fetchone()
    if admin:
        if admin['is_archived']:
            cursor.execute("UPDATE users SET is_active=TRUE, is_archived=FALSE WHERE id=%s AND role='admin'", (admin_id,))
                                           
            cursor.execute("UPDATE users SET is_active=TRUE WHERE role='voter' AND college_id=%s", (admin['college_id'],))
            conn.commit()
            flash("Admin restored!", "success")
        else:
            cursor.execute("UPDATE users SET is_active=FALSE, is_archived=TRUE WHERE id=%s AND role='admin'", (admin_id,))
                                              
            cursor.execute("UPDATE users SET is_active=FALSE WHERE role='voter' AND college_id=%s", (admin['college_id'],))
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
    cursor.execute("SELECT is_active, college_id FROM users WHERE id=%s AND role='admin'", (admin_id,))
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
                                      
        cursor.execute("UPDATE users SET is_active=%s WHERE role='voter' AND college_id=%s", (new_status, admin['college_id']))
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
    page = max(1, int(request.args.get('page', 1) or 1))
    per_page = 15
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action_type', '').strip()

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    base_where = "WHERE (u.role IN ('admin', 'superadmin') OR l.user_id IS NULL)"
    params = []
    if search:
        base_where += " AND (l.action LIKE %s OR l.details LIKE %s OR l.ip_address LIKE %s)"
        sp = f"%{search}%"
        params.extend([sp, sp, sp])
    if action_filter:
        base_where += " AND l.action = %s"
        params.append(action_filter.lower())

    cursor.execute(f"SELECT COUNT(*) as total FROM system_logs l LEFT JOIN users u ON l.user_id = u.id {base_where}", params)
    total_logs = cursor.fetchone()['total']
    total_pages = max(1, (total_logs + per_page - 1) // per_page)
    page = min(page, total_pages)

    cursor.execute(f"""
        SELECT l.*, u.firstname, u.surname, u.student_id, u.role,
               CONCAT(COALESCE(u.firstname,''), ' ', COALESCE(u.surname,'')) AS user
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        {base_where}
        ORDER BY l.created_at DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, (page - 1) * per_page])
    logs = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT l.action FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        WHERE (u.role IN ('admin', 'superadmin') OR l.user_id IS NULL)
        AND l.action IS NOT NULL
        ORDER BY l.action
    """)
    action_types = [r['action'] for r in cursor.fetchall()]

    cursor.close()
    conn.close()
    return render_template('system_logs.html', logs=logs, search=search, action_filter=action_filter,
                           action_types=action_types, page=page, total_pages=total_pages,
                           total_logs=total_logs, per_page=per_page, current_page=page)

@superadmin_bp.route("/profile")
@superadmin_required
def profile():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    admin = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin'")
    total_admins = (cursor.fetchone() or {}).get("cnt", 0)

    cursor.execute("SELECT COUNT(*) AS cnt FROM colleges")
    total_colleges = (cursor.fetchone() or {}).get("cnt", 0)

    cursor.close()
    conn.close()
    return render_template(
        "sa_profile.html",
        admin=admin,
        total_admins=total_admins,
        total_colleges=total_colleges
    )


@superadmin_bp.route("/profile/update", methods=["POST"])
@superadmin_required
def update_profile():
    form_type = request.form.get("form_type")
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    if form_type == "info":
        firstname  = request.form.get("firstname",  "").strip()
        middlename = request.form.get("middlename", "").strip()
        surname    = request.form.get("surname",    "").strip()
        email      = request.form.get("email",      "").strip()

        if not firstname or not surname or not email:
            flash("First name, surname, and email are required.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for("super_admin.profile"))

        cursor.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s",
            (email, session["user_id"])
        )
        if cursor.fetchone():
            flash("That email address is already in use.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for("super_admin.profile"))

        cursor.execute(
            """UPDATE users SET firstname=%s, middlename=%s, surname=%s, email=%s
               WHERE id=%s""",
            (firstname, middlename or None, surname, email, session["user_id"])
        )
        conn.commit()
        session["fullname"] = " ".join(filter(None, [firstname, middlename, surname])).strip()
        flash("Profile updated successfully.", "success")

    elif form_type == "password":
        from werkzeug.security import check_password_hash, generate_password_hash
        current_password  = request.form.get("current_password",  "")
        new_password      = request.form.get("new_password",      "")
        confirm_password  = request.form.get("confirm_password",  "")

        cursor.execute("SELECT password FROM users WHERE id = %s", (session["user_id"],))
        row = cursor.fetchone()

        if not row or not check_password_hash(row["password"], current_password):
            flash("Current password is incorrect.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for("super_admin.profile"))

        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for("super_admin.profile"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for("super_admin.profile"))

        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (generate_password_hash(new_password), session["user_id"])
        )
        conn.commit()
        flash("Password updated successfully.", "success")

    else:
        flash("Invalid request.", "danger")

    cursor.close()
    conn.close()
    return redirect(url_for("super_admin.profile"))