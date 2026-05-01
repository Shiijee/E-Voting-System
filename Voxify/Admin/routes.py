from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
from Voxify.Authentication.routes import admin_required
import os
from werkzeug.utils import secure_filename
import uuid

admin_bp = Blueprint('admin', __name__, 
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/admin/static')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'candidates')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_candidate_photo(file):
    """Save uploaded photo and return the filename"""
    if file and allowed_file(file.filename):
        try:
            # Create upload folder if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Generate unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"candidate_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save file
            file.save(filepath)
            return filename
        except Exception as e:
            print(f"Error saving photo: {e}")
            return None
    return None

def delete_candidate_photo(photo_filename):
    """Delete candidate photo file"""
    if photo_filename:
        try:
            filepath = os.path.join(UPLOAD_FOLDER, photo_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting photo: {e}")

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

    if college_id is not None:
        cursor.execute("SELECT COUNT(*) as total FROM elections WHERE college_id=%s", (college_id,))
        total_elections = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status='active' AND college_id=%s", (college_id,))
        active_elections = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND college_id=%s", (college_id,))
        total_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=FALSE AND college_id=%s", (college_id,))
        pending_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=TRUE AND college_id=%s", (college_id,))
        approved_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_active=FALSE AND college_id=%s", (college_id,))
        archived_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status='closed' AND college_id=%s", (college_id,))
        closed_elections = cursor.fetchone()['total']

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

        cursor.execute("""
            SELECT id, title, status, start_date, end_date, created_at
            FROM elections
            WHERE college_id=%s
            ORDER BY created_at DESC
            LIMIT 5
        """, (college_id,))
        recent_elections = cursor.fetchall()
    else:
        cursor.execute("SELECT COUNT(*) as total FROM elections")
        total_elections = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status='active'")
        active_elections = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter'")
        total_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=FALSE")
        pending_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=TRUE")
        approved_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_active=FALSE")
        archived_voters = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM elections WHERE status='closed'")
        closed_elections = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM candidates c
            JOIN positions p ON c.position_id = p.id
            JOIN elections e ON p.election_id = e.id
        """)
        total_candidates = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM votes v
            JOIN elections e ON v.election_id = e.id
        """)
        total_votes = cursor.fetchone()['total']

        cursor.execute("""
            SELECT id, title, status, start_date, end_date, created_at
            FROM elections
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_elections = cursor.fetchall()

    cursor.execute("""
        SELECT l.id, l.action, l.details, l.created_at,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 5
    """)
    recent_logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("dashboard.html",
                         college=college,
                         total_elections=total_elections,
                         active_elections=active_elections,
                         total_voters=total_voters,
                         pending_voters=pending_voters,
                         approved_voters=approved_voters,
                         archived_voters=archived_voters,
                         closed_elections=closed_elections,
                         total_candidates=total_candidates,
                         total_votes=total_votes,
                         recent_elections=recent_elections,
                         recent_logs=recent_logs)

# ============================================
# ELECTION MANAGEMENT
# ============================================

@admin_bp.route("/elections")
@admin_required
def view_elections():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    # Show elections for this college or elections with no college assigned
    if college_id is not None:
        cursor.execute("SELECT * FROM elections WHERE college_id=%s OR college_id IS NULL ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT * FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()

    if college_id is not None:
        cursor.execute("""
            SELECT p.election_id,
                   p.id AS position_id,
                   p.title AS position_title,
                   p.display_order,
                   c.id AS candidate_id,
                   c.firstname,
                   c.middlename,
                   c.surname,
                   c.student_id,
                   c.platform,
                   c.photo
            FROM positions p
            LEFT JOIN candidates c ON c.position_id = p.id
            JOIN elections e ON p.election_id = e.id
            WHERE e.college_id=%s OR e.college_id IS NULL
            ORDER BY e.created_at DESC, p.display_order, p.title, c.surname
        """, (college_id,))
    else:
        cursor.execute("""
            SELECT p.election_id,
                   p.id AS position_id,
                   p.title AS position_title,
                   p.display_order,
                   c.id AS candidate_id,
                   c.firstname,
                   c.middlename,
                   c.surname,
                   c.student_id,
                   c.platform,
                   c.photo
            FROM positions p
            LEFT JOIN candidates c ON c.position_id = p.id
            JOIN elections e ON p.election_id = e.id
            ORDER BY e.created_at DESC, p.display_order, p.title, c.surname
        """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    positions_by_election = {}
    for row in rows:
        election_positions = positions_by_election.setdefault(row['election_id'], [])
        if not election_positions or election_positions[-1]['position_id'] != row['position_id']:
            election_positions.append({
                'position_id': row['position_id'],
                'title': row['position_title'],
                'display_order': row['display_order'],
                'candidates': []
            })
        if row['candidate_id']:
            election_positions[-1]['candidates'].append({
                'id': row['candidate_id'],
                'fullname': f"{row['firstname'] or ''} {row['middlename'] or ''} {row['surname'] or ''}".strip(),
                'student_id': row['student_id'],
                'platform': row['platform'],
                'photo': row['photo']
            })

    return render_template('elections.html', elections=elections, positions_by_election=positions_by_election)

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

@admin_bp.route("/elections/<int:election_id>/positions")
@admin_required
def election_positions(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    # Get election details
    if college_id is not None:
        cursor.execute("SELECT * FROM elections WHERE id=%s AND (college_id=%s OR college_id IS NULL)", (election_id, college_id))
    else:
        cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()
    
    if not election:
        flash("Election not found!", "error")
        return redirect(url_for('admin.view_elections'))
    
    # Get positions with candidates for this election
    cursor.execute("""
        SELECT p.id AS position_id,
               p.title AS position_title,
               p.description,
               p.display_order,
               COUNT(c.id) AS candidate_count,
               GROUP_CONCAT(
                   CONCAT(
                       c.id, '|',
                       c.firstname, '|',
                       c.middlename, '|',
                       c.surname, '|',
                       c.student_id, '|',
                       COALESCE(c.platform, ''), '|',
                       COALESCE(c.photo, '')
                   ) SEPARATOR ';;'
               ) AS candidates_list
        FROM positions p
        LEFT JOIN candidates c ON c.position_id = p.id
        WHERE p.election_id=%s
        GROUP BY p.id, p.title, p.description, p.display_order
        ORDER BY p.display_order, p.title
    """, (election_id,))
    positions = cursor.fetchall()
    
    # Parse candidates data
    positions_data = []
    for pos in positions:
        candidates = []
        if pos['candidates_list']:
            for candidate_str in pos['candidates_list'].split(';;'):
                parts = candidate_str.split('|')
                if len(parts) >= 7:
                    candidates.append({
                        'id': parts[0],
                        'firstname': parts[1],
                        'middlename': parts[2],
                        'surname': parts[3],
                        'student_id': parts[4],
                        'platform': parts[5],
                        'photo': parts[6],
                        'fullname': f"{parts[1]} {parts[2]} {parts[3]}".strip()
                    })
        
        positions_data.append({
            'position_id': pos['position_id'],
            'title': pos['position_title'],
            'description': pos['description'],
            'display_order': pos['display_order'],
            'candidate_count': pos['candidate_count'],
            'candidates': candidates
        })
    
    cursor.close()
    conn.close()
    
    return render_template('election_positions.html', election=election, positions=positions_data)

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
        if college_id is not None:
            cursor.execute(
                "UPDATE elections SET title=%s, description=%s, start_date=%s, end_date=%s WHERE id=%s AND college_id=%s",
                (title, description, start_date, end_date, election_id, college_id)
            )
        else:
            cursor.execute(
                "UPDATE elections SET title=%s, description=%s, start_date=%s, end_date=%s WHERE id=%s AND college_id IS NULL",
                (title, description, start_date, end_date, election_id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Election updated successfully!", "success")
        return redirect(url_for('admin.view_elections'))
    
    if college_id is not None:
        cursor.execute("SELECT * FROM elections WHERE id=%s AND (college_id=%s OR college_id IS NULL)", (election_id, college_id))
    else:
        cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
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
    if college_id is not None:
        cursor.execute("UPDATE elections SET status='active' WHERE id=%s AND college_id=%s", (election_id, college_id))
    else:
        cursor.execute("UPDATE elections SET status='active' WHERE id=%s AND college_id IS NULL", (election_id,))
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
    if college_id is not None:
        cursor.execute("UPDATE elections SET status='completed' WHERE id=%s AND college_id=%s", (election_id, college_id))
    else:
        cursor.execute("UPDATE elections SET status='completed' WHERE id=%s AND college_id IS NULL", (election_id,))
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
    if college_id is not None:
        cursor.execute("DELETE FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
    else:
        cursor.execute("DELETE FROM elections WHERE id=%s AND college_id IS NULL", (election_id,))
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
    if college_id is not None:
        cursor.execute("""
            SELECT p.*, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.college_id=%s OR e.college_id IS NULL
            ORDER BY e.created_at DESC, p.display_order
        """, (college_id,))
        positions = cursor.fetchall()
        cursor.execute("SELECT id, title FROM elections WHERE status != 'completed' AND (college_id=%s OR college_id IS NULL)", (college_id,))
    else:
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
    college_id = get_admin_college_id()
    if request.method == "POST":
        election_id = request.form["election_id"]
        title = request.form["title"]
        description = request.form["description"]
        max_votes = request.form.get("max_votes", 1)
        display_order = request.form.get("display_order", 0)
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor()
        if college_id is not None:
            cursor.execute(
                "SELECT id FROM elections WHERE id=%s AND college_id=%s",
                (election_id, college_id)
            )
            if cursor.fetchone() is None:
                cursor.close()
                conn.close()
                flash("Selected election not found for your college.", "error")
                return redirect(url_for('admin.view_positions'))
        
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
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE status != 'completed' AND (college_id=%s OR college_id IS NULL)", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections WHERE status != 'completed'")
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('position_form.html', action='add', position=None, elections=elections)


@admin_bp.route("/positions/<int:position_id>/edit", methods=["POST"])
@admin_required
def edit_position(position_id):
    college_id = get_admin_college_id()
    election_id = request.form["election_id"]
    title = request.form["title"]
    description = request.form.get("description", "")
    max_votes = request.form.get("max_votes", 1)
    display_order = request.form.get("display_order", 0)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    if college_id is not None:
        cursor.execute(
            """UPDATE positions p JOIN elections e ON p.election_id = e.id
               SET p.title=%s, p.description=%s, p.max_votes=%s, p.display_order=%s, p.election_id=%s
               WHERE p.id=%s AND e.college_id=%s""",
            (title, description, max_votes, display_order, election_id, position_id, college_id)
        )
    else:
        cursor.execute(
            "UPDATE positions SET title=%s, description=%s, max_votes=%s, display_order=%s, election_id=%s WHERE id=%s",
            (title, description, max_votes, display_order, election_id, position_id)
        )
    conn.commit()
    cursor.close()
    conn.close()
    flash("Position updated successfully!", "success")
    return redirect(url_for('admin.view_positions'))

@admin_bp.route("/positions/<int:position_id>/delete")
@admin_required
def delete_position(position_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    if college_id is not None:
        cursor.execute(
            "DELETE p FROM positions p JOIN elections e ON p.election_id = e.id WHERE p.id=%s AND e.college_id=%s",
            (position_id, college_id)
        )
    else:
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
    election_id = request.args.get('election_id')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    # Load all elections for the dropdown filter
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE college_id=%s OR college_id IS NULL ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()

    query = """
        SELECT c.*, p.title as position_title, e.title as election_title 
        FROM candidates c 
        JOIN positions p ON c.position_id = p.id  
        JOIN elections e ON p.election_id = e.id  
    """
    params = []
    conditions = []

    if college_id is not None:
        conditions.append("(e.college_id=%s OR e.college_id IS NULL)")
        params.append(college_id)
    if election_id:
        conditions.append("e.id=%s")
        params.append(election_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY e.created_at DESC, p.display_order"
    cursor.execute(query, tuple(params))
    candidates = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('candidates.html', candidates=candidates, elections=elections, selected_election_id=election_id)

@admin_bp.route("/candidates/new", methods=["GET", "POST"])
@admin_required
def create_candidate():
    college_id = get_admin_college_id()
    if request.method == "POST":
        position_id = request.form["position_id"]
        firstname = request.form["firstname"]
        middlename = request.form.get("middlename", "")
        surname = request.form["surname"]
        platform = request.form.get("platform", "")
        partylist = request.form.get("partylist", "")
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        if college_id is not None:
            cursor.execute(
                "SELECT p.id FROM positions p JOIN elections e ON p.election_id = e.id WHERE p.id=%s AND e.college_id=%s",
                (position_id, college_id)
            )
            if cursor.fetchone() is None:
                cursor.close()
                conn.close()
                flash("Selected position does not belong to your college.", "error")
                return redirect(url_for('admin.view_candidates'))

        # Auto-generate student_id: voter{college_id}({n})
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM candidates WHERE college_id=%s",
            (college_id,)
        )
        row = cursor.fetchone()
        next_n = (row['cnt'] if row else 0) + 1
        student_id = f"voter{college_id}({next_n})"
        
        # Handle photo upload
        photo_filename = None
        if 'photo' in request.files and request.files['photo'].filename != '':
            photo_filename = save_candidate_photo(request.files['photo'])
        
        cursor.execute(
            """INSERT INTO candidates (position_id, student_id, firstname, middlename, surname, platform, partylist, status, college_id, photo) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved', %s, %s)""",
            (position_id, student_id, firstname, middlename, surname, platform, partylist, college_id, photo_filename)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Candidate added successfully!", "success")
        return redirect(url_for('admin.view_candidates'))
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE college_id=%s OR college_id IS NULL ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()

    if college_id is not None:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status != 'completed' AND (e.college_id=%s OR e.college_id IS NULL)
        """, (college_id,))
    else:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status != 'completed'
        """)
    positions = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('candidate_form.html', action='add', candidate=None, positions=positions, voters=[], elections=elections)

@admin_bp.route("/candidates/<int:candidate_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_candidate(candidate_id):
    college_id = get_admin_college_id()
    if request.method == "POST":
        position_id = request.form["position_id"]
        firstname = request.form["firstname"]
        middlename = request.form.get("middlename", "")
        surname = request.form["surname"]
        platform = request.form.get("platform", "")
        partylist = request.form.get("partylist", "")
        
        conn = current_app.config["get_db_connection"]()
        cursor = conn.cursor(dictionary=True)
        
        # Get current candidate to preserve existing student_id and photo
        if college_id is not None:
            cursor.execute("SELECT * FROM candidates WHERE id=%s AND college_id=%s", (candidate_id, college_id))
        else:
            cursor.execute("SELECT * FROM candidates WHERE id=%s AND college_id IS NULL", (candidate_id,))
        candidate = cursor.fetchone()
        
        photo_filename = candidate.get('photo') if candidate else None
        # Preserve the auto-generated student_id; do not overwrite it
        student_id = candidate.get('student_id') if candidate else None
        
        # Handle photo upload
        if 'photo' in request.files and request.files['photo'].filename != '':
            # Delete old photo if exists
            if photo_filename:
                delete_candidate_photo(photo_filename)
            # Save new photo
            photo_filename = save_candidate_photo(request.files['photo'])
        
        cursor.execute(
            """UPDATE candidates SET position_id=%s, student_id=%s, firstname=%s, middlename=%s, 
               surname=%s, platform=%s, partylist=%s, photo=%s WHERE id=%s AND college_id=%s""",
            (position_id, student_id, firstname, middlename, surname, platform, partylist, photo_filename, candidate_id, college_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Candidate updated successfully!", "success")
        return redirect(url_for('admin.view_candidates'))
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    # Get candidate data
    if college_id is not None:
        cursor.execute("""
            SELECT c.*, p.election_id
            FROM candidates c
            LEFT JOIN positions p ON c.position_id = p.id
            WHERE c.id=%s AND c.college_id=%s
        """, (candidate_id, college_id))
    else:
        cursor.execute("""
            SELECT c.*, p.election_id
            FROM candidates c
            LEFT JOIN positions p ON c.position_id = p.id
            WHERE c.id=%s AND c.college_id IS NULL
        """, (candidate_id,))
    candidate = cursor.fetchone()
    
    if not candidate:
        cursor.close()
        conn.close()
        flash("Candidate not found!", "error")
        return redirect(url_for('admin.view_candidates'))
    
    # Get positions
    if college_id is not None:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status != 'completed' AND (e.college_id=%s OR e.college_id IS NULL)
        """, (college_id,))
    else:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status != 'completed'
        """)
    positions = cursor.fetchall()

    # Load all elections for the dropdown filter
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE college_id=%s OR college_id IS NULL ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('candidate_form.html', action='edit', candidate=candidate, positions=positions, voters=[], elections=elections)

@admin_bp.route("/candidates/<int:candidate_id>/delete")
@admin_required
def delete_candidate(candidate_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    if college_id is not None:
        cursor.execute("SELECT photo FROM candidates WHERE id=%s AND college_id=%s", (candidate_id, college_id))
    else:
        cursor.execute("SELECT photo FROM candidates WHERE id=%s", (candidate_id,))
    candidate = cursor.fetchone()
    
    # Delete photo if it exists
    if candidate and candidate.get('photo'):
        delete_candidate_photo(candidate['photo'])
    
    if college_id is not None:
        cursor.execute("DELETE FROM candidates WHERE id=%s AND college_id=%s", (candidate_id, college_id))
    else:
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
    
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE college_id=%s OR college_id IS NULL ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections ORDER BY created_at DESC")
    elections = cursor.fetchall()
    
    selected_election = None
    results = []
    total_votes = 0
    total_voters_voted = 0
    
    if election_id:
        if college_id is not None:
            cursor.execute("SELECT * FROM elections WHERE id=%s AND (college_id=%s OR college_id IS NULL)", (election_id, college_id))
        else:
            cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
        selected_election = cursor.fetchone()
        
        if selected_election:
            cursor.execute("""
                SELECT 
                    p.id AS position_id,
                    p.title AS position_title,
                    c.id AS candidate_id,
                    c.firstname,
                    c.middlename,
                    c.surname,
                    c.student_id,
                    COALESCE(c.platform, '') AS platform,
                    COALESCE(c.photo, '') AS photo,
                    COUNT(v.id) AS vote_count
                FROM positions p
                LEFT JOIN candidates c ON c.position_id = p.id
                LEFT JOIN votes v ON v.candidate_id = c.id AND v.election_id = %s
                WHERE p.election_id = %s
                GROUP BY p.id, p.title, c.id, c.firstname, c.middlename, c.surname, c.student_id, c.platform, c.photo
                ORDER BY p.display_order, vote_count DESC
            """, (election_id, election_id))
            rows = cursor.fetchall()

            positions = {}
            for row in rows:
                position_data = positions.setdefault(row['position_id'], {
                    'position': {'title': row['position_title']},
                    'candidates': [],
                    'total_votes': 0
                })

                if row['candidate_id'] is not None:
                    full_name = ' '.join(filter(None, [row['firstname'], row['middlename'], row['surname']])).strip()
                    position_data['candidates'].append({
                        'vote_count': row['vote_count'],
                        'candidate': {
                            'full_name': full_name or 'Unknown Candidate',
                            'partylist': None,
                            'student_id': row['student_id'],
                            'photo': row['photo']
                        }
                    })
                    position_data['total_votes'] += row['vote_count'] or 0

            for position in positions.values():
                if position['total_votes'] > 0:
                    for candidate in position['candidates']:
                        candidate['percentage'] = round((candidate['vote_count'] / position['total_votes']) * 100, 1)
                else:
                    for candidate in position['candidates']:
                        candidate['percentage'] = 0.0

            results = list(positions.values())
            total_votes = sum(p['total_votes'] for p in results)
            cursor.execute("SELECT COUNT(DISTINCT voter_id) as total FROM votes WHERE election_id=%s", (election_id,))
            total_voters_voted = cursor.fetchone()['total'] or 0
    
    cursor.close()
    conn.close()
    
    return render_template('results.html', elections=elections, election_id=election_id,
                         selected_election=selected_election, results=results,
                         total_votes=total_votes, total_voters_voted=total_voters_voted)

@admin_bp.route("/logs")
@admin_required
def view_logs():
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action_filter', '').strip() or None
    action_types = ['login', 'logout', 'vote', 'create_election', 'create_position', 'edit_election', 'delete_election']

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT l.id, l.action, l.details, l.created_at, l.ip_address,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        WHERE 1=1
    """
    params = []

    if action_filter:
        query += " AND l.action = %s"
        params.append(action_filter)

    if search:
        query += " AND (l.action LIKE %s OR l.details LIKE %s OR u.firstname LIKE %s OR u.surname LIKE %s OR l.ip_address LIKE %s)"
        like_search = f"%{search}%"
        params.extend([like_search] * 5)

    query += " ORDER BY l.created_at DESC LIMIT 500"
    cursor.execute(query, params)
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'logs.html',
        logs=logs,
        search=search,
        action_filter=action_filter,
        action_types=action_types
    )


# ============================================
# NOTIFICATIONS API
# ============================================

from flask import jsonify
import math

@admin_bp.route("/api/notifications")
@admin_required
def api_notifications():
    """Return recent important system log events as notifications."""
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT l.id, l.action, l.details, l.created_at,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 15
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    def time_ago(dt):
        if not dt:
            return ''
        now = datetime.now()
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return 'Just now'
        mins = secs // 60
        if mins < 60:
            return f'{mins} min ago'
        hrs = mins // 60
        if hrs < 24:
            return f'{hrs} hr ago'
        days = hrs // 24
        return f'{days} day{"s" if days > 1 else ""} ago'

    def classify(action):
        a = (action or '').lower()
        if 'delete' in a or 'remove' in a or 'error' in a:
            return 'red', 'bi-exclamation-triangle-fill'
        if 'login' in a:
            return 'green', 'bi-shield-check'
        if 'logout' in a:
            return 'gray', 'bi-box-arrow-right'
        if 'create' in a or 'add' in a:
            return 'blue', 'bi-plus-circle-fill'
        if 'update' in a or 'edit' in a:
            return 'amber', 'bi-pencil-fill'
        if 'vote' in a:
            return 'blue', 'bi-check2-circle'
        return 'gray', 'bi-info-circle-fill'

    notifications = []
    for row in rows:
        color, icon = classify(row['action'])
        action_label = (row['action'] or '').replace('_', ' ').title()
        user = (row['user_name'] or '').strip() or 'System'
        detail = row['details'] or ''
        text = f"{action_label}"
        if user and user != 'System':
            text += f" by {user}"
        if detail:
            text += f" — {detail[:60]}{'…' if len(detail) > 60 else ''}"
        notifications.append({
            'id': row['id'],
            'text': text,
            'icon': icon,
            'type': color,
            'time': time_ago(row['created_at']),
            'read': False
        })

    return jsonify(notifications)


# ============================================
# VOTER MANAGEMENT (ADMIN CREATES VOTERS)
# ============================================