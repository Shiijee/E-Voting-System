from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
from Voxify.Authentication.routes import admin_required

admin_bp = Blueprint('admin', __name__, 
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/admin/static')

def get_admin_college_id():
    """Get the college_id of the currently logged-in admin."""
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT college_id FROM users WHERE id=%s", (session['user_id'],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['college_id'] if result else None

# ============================================
# DASHBOARD
# ============================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    # Get college info
    college = None
    if college_id:
        cursor.execute("SELECT name FROM colleges WHERE id=%s", (college_id,))
        college = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as total FROM elections WHERE college_id=%s", (college_id,))
    total_elections = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status='active' AND college_id=%s", (college_id,))
    active_elections = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=FALSE AND college_id=%s", (college_id,))
    pending_voters = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=TRUE AND college_id=%s", (college_id,))
    approved_voters = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM candidates c
        JOIN positions p ON c.position_id = p.id
        JOIN elections e ON p.election_id = e.id
        WHERE e.college_id=%s
    """, (college_id,))
    total_candidates = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(*) as total FROM votes v
        JOIN elections e ON v.election_id = e.id
        WHERE e.college_id=%s
    """, (college_id,))
    total_votes = cursor.fetchone()['total']
    
    cursor.close()
    conn.close()
    
    return render_template("dashboard.html",
                         college=college,
                         total_elections=total_elections,
                         active_elections=active_elections,
                         pending_voters=pending_voters,
                         approved_voters=approved_voters,
                         total_candidates=total_candidates,
                         total_votes=total_votes)

# ============================================
# ELECTION MANAGEMENT
# ============================================

@admin_bp.route("/elections")
@admin_required
def view_elections():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM elections WHERE college_id=%s ORDER BY created_at DESC", (college_id,))
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('elections.html', elections=elections)

@admin_bp.route("/elections/new", methods=["GET", "POST"])
@admin_required
def create_election():
    college_id = get_admin_college_id()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO elections (title, description, start_date, end_date, created_by, college_id, status) 
               VALUES (%s, %s, %s, %s, %s, %s, 'upcoming')""",
            (title, description, start_date, end_date, session['user_id'], college_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Election created successfully!", "success")
        return redirect(url_for('admin.view_elections'))
    
    return render_template('election_form.html', action='add', election=None)

@admin_bp.route("/elections/<int:election_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        cursor.execute(
            "UPDATE elections SET title=%s, description=%s, start_date=%s, end_date=%s WHERE id=%s AND college_id=%s",
            (title, description, start_date, end_date, election_id, college_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Election updated successfully!", "success")
        return redirect(url_for('admin.view_elections'))
    
    cursor.execute("SELECT * FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
    election = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('election_form.html', action='edit', election=election)

@admin_bp.route("/elections/<int:election_id>/activate")
@admin_required
def activate_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='active' WHERE id=%s AND college_id=%s", (election_id, college_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election activated!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/deactivate")
@admin_required
def deactivate_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='completed' WHERE id=%s AND college_id=%s", (election_id, college_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election completed!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/delete")
@admin_required
def delete_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election deleted!", "success")
    return redirect(url_for('admin.view_elections'))

# ============================================
# POSITION MANAGEMENT
# ============================================

@admin_bp.route("/positions")
@admin_required
def view_positions():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, e.title as election_title 
        FROM positions p 
        JOIN elections e ON p.election_id = e.id 
        WHERE e.college_id=%s
        ORDER BY e.created_at DESC, p.display_order
    """, (college_id,))
    positions = cursor.fetchall()
    
    cursor.execute("SELECT id, title FROM elections WHERE status != 'completed' AND college_id=%s", (college_id,))
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('positions.html', positions=positions, elections=elections)

@admin_bp.route("/positions/new", methods=["GET", "POST"])
@admin_required
def create_position():
    college_id = get_admin_college_id()
    if request.method == "POST":
        election_id = request.form["election_id"]
        title = request.form["title"]
        description = request.form["description"]
        max_votes = request.form.get("max_votes", 1)
        display_order = request.form.get("display_order", 0)
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO positions (election_id, title, description, max_votes, display_order, college_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (election_id, title, description, max_votes, display_order, college_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Position created successfully!", "success")
        return redirect(url_for('admin.view_positions'))
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title FROM elections WHERE status != 'completed' AND college_id=%s", (college_id,))
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('position_form.html', action='add', position=None, elections=elections)

@admin_bp.route("/positions/<int:position_id>/delete")
@admin_required
def delete_position(position_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM positions WHERE id=%s", (position_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Position deleted!", "success")
    return redirect(url_for('admin.view_positions'))

# ============================================
# CANDIDATE MANAGEMENT
# ============================================

@admin_bp.route("/candidates")
@admin_required
def view_candidates():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, p.title as position_title, e.title as election_title 
        FROM candidates c 
        JOIN positions p ON c.position_id = p.id 
        JOIN elections e ON p.election_id = e.id 
        WHERE e.college_id=%s
        ORDER BY e.created_at DESC, p.display_order
    """, (college_id,))
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('candidates.html', candidates=candidates)

@admin_bp.route("/candidates/new", methods=["GET", "POST"])
@admin_required
def create_candidate():
    college_id = get_admin_college_id()
    if request.method == "POST":
        position_id = request.form["position_id"]
        student_id = request.form["student_id"]
        firstname = request.form["firstname"]
        middlename = request.form.get("middlename", "")
        surname = request.form["surname"]
        platform = request.form.get("platform", "")
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO candidates (position_id, student_id, firstname, middlename, surname, platform, status, college_id) 
               VALUES (%s, %s, %s, %s, %s, %s, 'approved', %s)""",
            (position_id, student_id, firstname, middlename, surname, platform, college_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Candidate added successfully!", "success")
        return redirect(url_for('admin.view_candidates'))
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id as position_id, p.title as position_title, e.title as election_title 
        FROM positions p 
        JOIN elections e ON p.election_id = e.id 
        WHERE e.status != 'completed' AND e.college_id=%s
    """, (college_id,))
    positions = cursor.fetchall()

    # Only show approved voters from this college as candidate options
    cursor.execute("""
        SELECT student_id, firstname, middlename, surname 
        FROM users WHERE role='voter' AND is_approved=TRUE AND college_id=%s
        ORDER BY surname
    """, (college_id,))
    voters = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('candidate_form.html', action='add', candidate=None, positions=positions, voters=voters)

@admin_bp.route("/candidates/<int:candidate_id>/delete")
@admin_required
def delete_candidate(candidate_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id=%s", (candidate_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Candidate deleted!", "success")
    return redirect(url_for('admin.view_candidates'))

# ============================================
# VOTER MANAGEMENT (ADMIN CREATES VOTERS)
# ============================================

@admin_bp.route("/voters")
@admin_required
def view_voters():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.*, c.name as college_name FROM users u
        LEFT JOIN colleges c ON u.college_id = c.id
        WHERE u.role='voter' AND u.college_id=%s
        ORDER BY u.created_at DESC
    """, (college_id,))
    voters = cursor.fetchall()
    cursor.close()
    conn.close()
    student_id_prefix = f"241-{college_id}-"
    return render_template('voters.html', voters=voters, student_id_prefix=student_id_prefix)

@admin_bp.route("/voters/create", methods=["POST"])
@admin_required
def create_voter():
    college_id = get_admin_college_id()
    firstname   = request.form["firstname"]
    middlename  = request.form.get("middlename", "")
    surname     = request.form["surname"]
    email       = request.form["email"]
    password    = request.form["password"]
    seq         = request.form.get("student_id_seq", "").strip()

    from werkzeug.security import generate_password_hash
    import re

    if not seq.isdigit():
        flash("Student ID sequence must be a number (e.g. 1, 2, 3).", "error")
        return redirect(url_for('admin.view_voters'))

    student_id = f"241-{college_id}-{seq.zfill(4)}"

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check for duplicate student_id
        cursor.execute("SELECT id FROM users WHERE student_id=%s", (student_id,))
        if cursor.fetchone():
            flash(f"Student ID {student_id} already exists. Please use a different number.", "error")
            return redirect(url_for('admin.view_voters'))

        cursor.execute(
            """INSERT INTO users (student_id, firstname, middlename, surname, email,
               password, role, college_id, is_approved, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, 'voter', %s, TRUE, TRUE)""",
            (student_id, firstname, middlename, surname, email,
             generate_password_hash(password), college_id)
        )
        conn.commit()
        flash(f"Voter {firstname} {surname} created successfully! (ID: {student_id})", "success")
    except Exception as e:
        flash(f"Error creating voter: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin.view_voters'))

@admin_bp.route("/voters/<int:voter_id>/edit", methods=["POST"])
@admin_required
def edit_voter(voter_id):
    college_id = get_admin_college_id()
    firstname  = request.form["firstname"]
    middlename = request.form.get("middlename", "")
    surname    = request.form["surname"]
    email      = request.form["email"]
    password   = request.form.get("password", "").strip()

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        if password:
            from werkzeug.security import generate_password_hash
            cursor.execute(
                """UPDATE users SET firstname=%s, middlename=%s, surname=%s, email=%s,
                   password=%s
                   WHERE id=%s AND role='voter' AND college_id=%s""",
                (firstname, middlename, surname, email,
                 generate_password_hash(password), voter_id, college_id)
            )
        else:
            cursor.execute(
                """UPDATE users SET firstname=%s, middlename=%s, surname=%s, email=%s
                   WHERE id=%s AND role='voter' AND college_id=%s""",
                (firstname, middlename, surname, email, voter_id, college_id)
            )
        conn.commit()
        flash("Voter updated successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin.view_voters'))

@admin_bp.route("/voters/<int:voter_id>/archive")
@admin_required
def archive_voter(voter_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_active FROM users WHERE id=%s AND role='voter' AND college_id=%s", (voter_id, college_id))
    voter = cursor.fetchone()
    if voter:
        new_status = not voter['is_active']
        cursor.execute("UPDATE users SET is_active=%s WHERE id=%s AND role='voter' AND college_id=%s",
                       (new_status, voter_id, college_id))
        conn.commit()
        flash("Voter archived!" if not new_status else "Voter restored!", "success")
    cursor.close()
    conn.close()
    return redirect(url_for('admin.view_voters'))

@admin_bp.route("/voters/<int:voter_id>/delete")
@admin_required
def delete_voter(voter_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='voter' AND college_id=%s", (voter_id, college_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Voter deleted permanently!", "success")
    return redirect(url_for('admin.view_voters'))

# ============================================
# RESULTS
# ============================================

@admin_bp.route("/results")
@admin_required
def view_results():
    college_id = get_admin_college_id()
    election_id = request.args.get('election_id', type=int)
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, title FROM elections WHERE college_id=%s ORDER BY created_at DESC", (college_id,))
    elections = cursor.fetchall()
    
    selected_election = None
    results = []
    total_votes = 0
    
    if election_id:
        cursor.execute("SELECT * FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
        selected_election = cursor.fetchone()
        
        if selected_election:
            cursor.execute("""
                SELECT 
                    p.title as position_title,
                    c.firstname, c.surname, c.student_id,
                    COUNT(v.id) as vote_count
                FROM positions p
                LEFT JOIN candidates c ON c.position_id = p.id
                LEFT JOIN votes v ON v.candidate_id = c.id AND v.election_id = %s
                WHERE p.election_id = %s
                GROUP BY c.id, p.title
                ORDER BY p.display_order, vote_count DESC
            """, (election_id, election_id))
            results = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(DISTINCT voter_id) as total FROM votes WHERE election_id=%s", (election_id,))
            total_votes = cursor.fetchone()['total'] or 0
    
    cursor.close()
    conn.close()
    
    return render_template('results.html', elections=elections, election_id=election_id,
                         selected_election=selected_election, results=results, total_votes=total_votes)

@admin_bp.route("/logs")
@admin_required
def view_logs():
    return render_template(
        'logs.html',
        logs=[],
        search='',
        action_filter=None,
        action_types=['login', 'logout', 'vote', 'create_election']
    )

# ============================================
# VOTER MANAGEMENT (ADMIN CREATES VOTERS)
# ============================================