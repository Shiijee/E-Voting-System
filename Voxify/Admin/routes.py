from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from Voxify.Authentication.routes import admin_required

admin_bp = Blueprint('admin', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/admin/static')


# ============================================
# DASHBOARD
# ============================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM elections")
    total_elections = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status = 'active'")
    active_elections = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'voter' AND is_approved = FALSE")
    pending_voters = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'voter' AND is_approved = TRUE")
    approved_voters = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM candidates")
    total_candidates = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM votes")
    total_votes = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template("dashboard.html",
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
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('elections.html', elections=elections)

@admin_bp.route("/elections/new", methods=["GET", "POST"])
@admin_required
def create_election():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO elections (title, description, start_date, end_date, created_by, status) VALUES (%s, %s, %s, %s, %s, 'upcoming')",
            (title, description, start_date, end_date, session['user_id'])
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
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        cursor.execute(
            "UPDATE elections SET title=%s, description=%s, start_date=%s, end_date=%s WHERE id=%s",
            (title, description, start_date, end_date, election_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Election updated successfully!", "success")
        return redirect(url_for('admin.view_elections'))

    cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('election_form.html', action='edit', election=election)

@admin_bp.route("/elections/<int:election_id>/activate")
@admin_required
def activate_election(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='active' WHERE id=%s", (election_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election activated!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/deactivate")
@admin_required
def deactivate_election(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='completed' WHERE id=%s", (election_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election completed!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/delete")
@admin_required
def delete_election(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM elections WHERE id=%s", (election_id,))
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
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, e.title as election_title
        FROM positions p
        JOIN elections e ON p.election_id = e.id
        ORDER BY e.created_at DESC, p.display_order
    """)
    positions = cursor.fetchall()

    cursor.execute("SELECT id, title FROM elections WHERE status != 'completed'")
    elections = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('positions.html', positions=positions, elections=elections)

@admin_bp.route("/positions/new", methods=["GET", "POST"])
@admin_required
def create_position():
    if request.method == "POST":
        election_id = request.form["election_id"]
        title = request.form["title"]
        description = request.form["description"]
        max_votes = request.form.get("max_votes", 1)
        display_order = request.form.get("display_order", 0)

        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO positions (election_id, title, description, max_votes, display_order) VALUES (%s, %s, %s, %s, %s)",
            (election_id, title, description, max_votes, display_order)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Position created successfully!", "success")
        return redirect(url_for('admin.view_positions'))

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title FROM elections WHERE status != 'completed'")
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
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, p.title as position_title, e.title as election_title
        FROM candidates c
        JOIN positions p ON c.position_id = p.id
        JOIN elections e ON p.election_id = e.id
        ORDER BY e.created_at DESC, p.display_order
    """)
    candidates = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('candidates.html', candidates=candidates)

@admin_bp.route("/candidates/new", methods=["GET", "POST"])
@admin_required
def create_candidate():
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
            """INSERT INTO candidates (position_id, student_id, firstname, middlename, surname, platform, status)
               VALUES (%s, %s, %s, %s, %s, %s, 'approved')""",
            (position_id, student_id, firstname, middlename, surname, platform)
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
        WHERE e.status = 'active'
    """)
    positions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('candidate_form.html', action='add', candidate=None, positions=positions)

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
# VOTER MANAGEMENT
# ============================================

@admin_bp.route("/voters")
@admin_required
def view_voters():
    status = request.args.get('status', 'all')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    base_query = "SELECT *, CASE WHEN is_approved=TRUE THEN 'Approved' ELSE 'Pending' END AS status FROM users WHERE role='voter'"
    if status == 'pending':
        cursor.execute(base_query + " AND is_approved=FALSE ORDER BY created_at DESC")
    elif status == 'approved':
        cursor.execute(base_query + " AND is_approved=TRUE ORDER BY created_at DESC")
    else:
        cursor.execute(base_query + " ORDER BY created_at DESC")

    voters = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('voters.html', voters=voters, status=status)

@admin_bp.route("/voters/<int:voter_id>/approve")
@admin_required
def approve_voter(voter_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved=TRUE WHERE id=%s AND role='voter'", (voter_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Voter approved!", "success")
    return redirect(url_for('admin.view_voters'))

@admin_bp.route("/voters/<int:voter_id>/reject")
@admin_required
def reject_voter(voter_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='voter'", (voter_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Voter rejected and removed!", "warning")
    return redirect(url_for('admin.view_voters'))

@admin_bp.route("/voters/<int:voter_id>/delete")
@admin_required
def delete_voter(voter_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='voter'", (voter_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Voter deleted!", "success")
    return redirect(url_for('admin.view_voters'))


# ============================================
# RESULTS
# ============================================

@admin_bp.route("/results")
@admin_required
def view_results():
    election_id = request.args.get('election_id', type=int)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()

    selected_election = None
    results = []
    total_votes = 0

    if election_id:
        cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
        selected_election = cursor.fetchone()

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


# ============================================
# LOGS
# ============================================

@admin_bp.route("/logs")
@admin_required
def view_logs():
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
    return render_template('logs.html', logs=logs,
                           search='', action_filter=None,
                           action_types=['login', 'logout', 'vote', 'create_election'])
