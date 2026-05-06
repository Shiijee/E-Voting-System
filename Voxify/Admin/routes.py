from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
from Voxify.Authentication.routes import admin_required
from Voxify.utils.election_status import sync_election_statuses
from Voxify.utils.otp import send_account_email
import os
import re
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
                                                      
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
                                      
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"candidate_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
                       
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


def normalize_name(name):
    return re.sub(r'\s+', ' ', name.strip())


def format_name(name):
    return ' '.join([p.capitalize() for p in normalize_name(name).split(' ') if p])


def is_valid_name(name, required=True):
    normalized = normalize_name(name)
    if not normalized:
        return not required
    if len(normalized) < 2:
        return False
    return all(re.fullmatch(r'[A-Za-zÀ-ÖØ-öø-ÿ]{2,}', part) for part in normalized.split(' '))

                                              
           
                                              

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

                      
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

    cursor.execute(f"""
        SELECT l.id, l.action, l.details, l.created_at,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        WHERE u.role='voter' AND u.college_id=%s
        ORDER BY l.created_at DESC
        LIMIT 5
    """, (college_id,))
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

                                              
                     
                                              

@admin_bp.route("/elections")
@admin_required
def view_elections():
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    sync_election_statuses(conn, college_id)

                                                                           
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

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            flash("Invalid date format.", "error")
            return render_template('election_form.html', action='add', election=None)

        now = datetime.now()
        if start_dt < now:
            flash("Start date and time cannot be in the past.", "error")
            return render_template('election_form.html', action='add', election=None)
        if end_dt <= start_dt:
            flash("End date and time must be after the start date and time.", "error")
            return render_template('election_form.html', action='add', election=None)

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
    
                          
    if college_id is not None:
        cursor.execute("SELECT * FROM elections WHERE id=%s AND (college_id=%s OR college_id IS NULL)", (election_id, college_id))
    else:
        cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()
    
    if not election:
        flash("Election not found!", "error")
        return redirect(url_for('admin.view_elections'))
    
                                                     
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
    
                                 
    cursor2 = conn.cursor(dictionary=True)

                                       
    cursor2.execute("SELECT COUNT(*) as total FROM votes WHERE election_id=%s", (election_id,))
    total_votes_cast = cursor2.fetchone()['total'] or 0

                               
    cursor2.execute("SELECT COUNT(DISTINCT voter_id) as total FROM votes WHERE election_id=%s", (election_id,))
    total_voters_voted = cursor2.fetchone()['total'] or 0

                                                       
    election_college_id = election.get('college_id')
    if election_college_id:
        cursor2.execute(
            "SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=1 AND is_active=1 AND college_id=%s",
            (election_college_id,)
        )
    else:
        cursor2.execute(
            "SELECT COUNT(*) as total FROM users WHERE role='voter' AND is_approved=1 AND is_active=1"
        )
    total_eligible_voters = cursor2.fetchone()['total'] or 0
    total_voters_not_voted = max(0, total_eligible_voters - total_voters_voted)

    cursor2.close()
    cursor.close()
    conn.close()
    
    return render_template('election_positions.html',
                           election=election,
                           positions=positions_data,
                           total_votes_cast=total_votes_cast,
                           total_voters_voted=total_voters_voted,
                           total_voters_not_voted=total_voters_not_voted,
                           total_eligible_voters=total_eligible_voters)

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

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for('admin.edit_election', election_id=election_id))

        now = datetime.now()
        if start_dt < now:
            flash("Start date and time cannot be in the past.", "error")
            return redirect(url_for('admin.edit_election', election_id=election_id))
        if end_dt <= start_dt:
            flash("End date and time must be after the start date and time.", "error")
            return redirect(url_for('admin.edit_election', election_id=election_id))

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
    from datetime import datetime as _dt
    return render_template('election_form.html', action='edit', election=election, now=_dt.now())

@admin_bp.route("/elections/<int:election_id>/activate")
@admin_required
def activate_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status, start_date, end_date, previous_status FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()
    is_draft = election and election['status'] == 'draft'

    if is_draft:
        # Use saved previous_status if available
        if election.get('previous_status'):
            new_status = election['previous_status']
        else:
            # Fallback: determine status based on dates
            now = datetime.now()
            start_date = election['start_date']
            end_date = election['end_date']
            if isinstance(start_date, str):
                try: start_date = datetime.fromisoformat(start_date)
                except: start_date = None
            if isinstance(end_date, str):
                try: end_date = datetime.fromisoformat(end_date)
                except: end_date = None

            if end_date and end_date < now:
                new_status = 'completed'
            elif start_date and start_date <= now:
                new_status = 'active'
            else:
                new_status = 'upcoming'
    else:
        new_status = 'active'

    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status=%s WHERE id=%s", (new_status, election_id))
    conn.commit()
    cursor.close()
    conn.close()
    if is_draft:
        flash(f"Election restored to {new_status}!", "success")
    else:
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

@admin_bp.route("/elections/<int:election_id>/pause")
@admin_required
def pause_election(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='paused' WHERE id=%s", (election_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election paused!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/resume")
@admin_required
def resume_election(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    cursor.execute("UPDATE elections SET status='active' WHERE id=%s", (election_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election resumed!", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/<int:election_id>/archive")
@admin_required
def archive_election(election_id):
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()
    previous_status = election['status'] if election else 'upcoming'
    cursor = conn.cursor()
    if college_id is not None:
        cursor.execute("UPDATE elections SET status='draft', previous_status=%s WHERE id=%s AND (college_id=%s OR college_id IS NULL)", (previous_status, election_id, college_id))
    else:
        cursor.execute("UPDATE elections SET status='draft', previous_status=%s WHERE id=%s", (previous_status, election_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Election moved to draft.", "success")
    return redirect(url_for('admin.view_elections'))

@admin_bp.route("/elections/auto-update", methods=["POST"])
@admin_required
def auto_update_elections():
    """Auto-open upcoming elections whose start_date has passed,
       and auto-close active elections whose end_date has passed."""
    from datetime import datetime
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    now = datetime.now()

    if college_id is not None:
        cursor.execute(
            "SELECT id, status, start_date, end_date FROM elections WHERE (college_id=%s OR college_id IS NULL) AND status IN ('upcoming','active')",
            (college_id,)
        )
    else:
        cursor.execute(
            "SELECT id, status, start_date, end_date FROM elections WHERE status IN ('upcoming','active')"
        )
    elections = cursor.fetchall()

    opened = closed = 0
    for e in elections:
        start = e['start_date']
        end   = e['end_date']
        if isinstance(start, str):
            try: start = datetime.fromisoformat(start)
            except: start = None
        if isinstance(end, str):
            try: end = datetime.fromisoformat(end)
            except: end = None

        if e['status'] == 'upcoming' and start and now >= start:
            cursor.execute("UPDATE elections SET status='active' WHERE id=%s", (e['id'],))
            opened += 1
        elif e['status'] == 'active' and end and now >= end:
            cursor.execute("UPDATE elections SET status='completed' WHERE id=%s", (e['id'],))
            closed += 1

    conn.commit()
    cursor.close()
    conn.close()

    from flask import jsonify
    return jsonify({"opened": opened, "closed": closed})

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
            WHERE e.status NOT IN ('completed', 'draft')
              AND (e.college_id=%s OR e.college_id IS NULL)
            ORDER BY e.created_at DESC, p.display_order
        """, (college_id,))
        positions = cursor.fetchall()
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'draft') AND (college_id=%s OR college_id IS NULL)", (college_id,))
    else:
        cursor.execute("""
            SELECT p.*, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status NOT IN ('completed', 'draft')
            ORDER BY e.created_at DESC, p.display_order
        """)
        positions = cursor.fetchall()
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'draft')")
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

                                              
                      
                                              

@admin_bp.route("/candidates")
@admin_required
def view_candidates():
    college_id = get_admin_college_id()
    election_id = request.args.get('election_id')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

                                                                                                              
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE (college_id=%s OR college_id IS NULL) ORDER BY created_at DESC", (college_id,))
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

                                                          
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM candidates WHERE college_id=%s",
            (college_id,)
        )
        row = cursor.fetchone()
        next_n = (row['cnt'] if row else 0) + 1
        student_id = f"voter{college_id}({next_n})"
        
                             
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
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'paused') AND (college_id=%s OR college_id IS NULL) ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'paused') ORDER BY created_at DESC")
    elections = cursor.fetchall()

    if college_id is not None:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status NOT IN ('completed', 'paused') AND (e.college_id=%s OR e.college_id IS NULL)
        """, (college_id,))
    else:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status NOT IN ('completed', 'paused')
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
        
                                                                         
        if college_id is not None:
            cursor.execute("SELECT * FROM candidates WHERE id=%s AND college_id=%s", (candidate_id, college_id))
        else:
            cursor.execute("SELECT * FROM candidates WHERE id=%s AND college_id IS NULL", (candidate_id,))
        candidate = cursor.fetchone()
        
        photo_filename = candidate.get('photo') if candidate else None
                                                                     
        student_id = candidate.get('student_id') if candidate else None
        
                             
        if 'photo' in request.files and request.files['photo'].filename != '':
                                        
            if photo_filename:
                delete_candidate_photo(photo_filename)
                            
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
    
                   
    if college_id is not None:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status NOT IN ('completed', 'paused') AND (e.college_id=%s OR e.college_id IS NULL)
        """, (college_id,))
    else:
        cursor.execute("""
            SELECT p.id as position_id, p.title as position_title, p.election_id, e.title as election_title 
            FROM positions p 
            JOIN elections e ON p.election_id = e.id 
            WHERE e.status NOT IN ('completed', 'paused')
        """)
    positions = cursor.fetchall()

                                                
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'paused') AND (college_id=%s OR college_id IS NULL) ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections WHERE status NOT IN ('completed', 'paused') ORDER BY created_at DESC")
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
    create_voter_restore = session.pop("create_voter_restore", None)
    return render_template('voters.html', voters=voters, student_id_prefix=student_id_prefix,
                           create_voter_restore=create_voter_restore)

@admin_bp.route("/voters/create", methods=["POST"])
@admin_required
def create_voter():
    college_id = get_admin_college_id()
    firstname   = normalize_name(request.form["firstname"])
    middlename  = normalize_name(request.form.get("middlename", ""))
    surname     = normalize_name(request.form["surname"])
    email       = request.form["email"]
    password    = request.form["password"]
    seq         = request.form.get("student_id_seq", "").strip()

    from werkzeug.security import generate_password_hash

    def save_form_and_redirect(msg):
        """Flash error, stash form values in session, redirect back."""
        flash(msg, "error")
        session["create_voter_restore"] = {
            "firstname": firstname,
            "middlename": middlename,
            "surname": surname,
            "email": email,
            "student_id_seq": seq,
        }
        return redirect(url_for('admin.view_voters'))

    if not is_valid_name(firstname, True) or not is_valid_name(surname, True) or not is_valid_name(middlename, False):
        return save_form_and_redirect("First name and surname are required; names must be letters and spaces only, with each word at least 2 letters. Middle name is optional.")

    firstname = format_name(firstname)
    middlename = format_name(middlename)
    surname = format_name(surname)

    if not seq.isdigit():
        return save_form_and_redirect("Student ID sequence must be a number (e.g. 1, 2, 3.)")

    student_id = f"241-{college_id}-{seq.zfill(4)}"

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    try:
                                        
        cursor.execute("SELECT id FROM users WHERE student_id=%s LIMIT 1", (student_id,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return save_form_and_redirect(f"Student ID {student_id} already exists. Please use a different number.")

        if email != email.lower():
            cursor.close(); conn.close()
            return save_form_and_redirect("Email must be in lowercase.")
        if '@' not in email:
            cursor.close(); conn.close()
            return save_form_and_redirect("Email must contain '@'.")
        local_part, domain = email.split('@', 1)
        if len(local_part) < 3:
            cursor.close(); conn.close()
            return save_form_and_redirect("Email local part must be at least 3 characters.")
        domain = domain.lower()
        allowed_domains = [
            'gmail.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
            'outlook.com', 'hotmail.com', 'live.com', 'msn.com', 'icloud.com',
            'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'zoho.com',
            'zoho.eu', 'aol.com', 'fastmail.com', 'gmx.com', 'mail.com', 'yandex.com',
            'pldtmail.com', 'pldtdsl.net', 'globe.com.ph', 'smart.com.ph'
        ]
        is_allowed = domain in allowed_domains or domain.endswith(('.edu', '.ph', '.edu.ph', '.gov.ph', '.microsoft.com'))
        if not is_allowed:
            cursor.close(); conn.close()
            return save_form_and_redirect("Email must be from an accepted provider (e.g., Gmail, Outlook, Yahoo, or .edu/.ph domains).")

        cursor.execute("SELECT id FROM users WHERE email=%s LIMIT 1", (email,))
        if cursor.fetchone():
            cursor.close(); conn.close()
            return save_form_and_redirect(f"The email address '{email}' is already registered. Please use a different email.")

        cursor.execute(
            """INSERT INTO users (student_id, firstname, middlename, surname, email,
               password, role, college_id, is_approved, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, 'voter', %s, TRUE, TRUE)""",
            (student_id, firstname, middlename, surname, email,
             generate_password_hash(password), college_id)
        )
        conn.commit()
        email_sent = False
        if email and '@' in email:
                                                                        
            display_id = seq.zfill(5)
            email_sent = send_account_email(
                email, 'voter', display_id, password,
                fullname=f"{firstname} {surname}",
                extra_info=f"College ID: {college_id}"
            )
        message = f"Voter {firstname} {surname} created successfully! (ID: {student_id})"
        if email_sent:
            message += " Email notification sent."
        else:
            message += " Could not send notification email."
        flash(message, "success")
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
    firstname  = normalize_name(request.form["firstname"])
    middlename = normalize_name(request.form.get("middlename", ""))
    surname    = normalize_name(request.form["surname"])
    email      = request.form["email"]
    password   = request.form.get("password", "").strip()

    if not is_valid_name(firstname, True) or not is_valid_name(surname, True) or not is_valid_name(middlename, False):
        flash("First name and surname are required; names must be letters and spaces only, with each word at least 2 letters. Middle name is optional.", "danger")
        return redirect(url_for('admin.view_voters'))

    firstname = format_name(firstname)
    middlename = format_name(middlename)
    surname = format_name(surname)

    if email != email.lower():
        flash("Email must be in lowercase.", "danger")
        return redirect(url_for('admin.view_voters'))
    if '@' not in email:
        flash("Email must contain '@'.", "danger")
        return redirect(url_for('admin.view_voters'))
    local_part, domain = email.split('@', 1)
    if len(local_part) < 3:
        flash("Email local part must be at least 3 characters.", "danger")
        return redirect(url_for('admin.view_voters'))
    domain = domain.lower()
    allowed_domains = [
        'gmail.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
        'outlook.com', 'hotmail.com', 'live.com', 'msn.com', 'icloud.com',
        'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'zoho.com',
        'zoho.eu', 'aol.com', 'fastmail.com', 'gmx.com', 'mail.com', 'yandex.com',
        'pldtmail.com', 'pldtdsl.net', 'globe.com.ph', 'smart.com.ph'
    ]
    is_allowed = domain in allowed_domains or domain.endswith(('.edu', '.ph', '.edu.ph', '.gov.ph', '.microsoft.com'))
    if not is_allowed:
        flash("Email must be from an accepted provider (e.g., Gmail, Outlook, Yahoo, or .edu/.ph domains).", "danger")
        return redirect(url_for('admin.view_voters'))

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email=%s AND id != %s LIMIT 1", (email, voter_id))
        if cursor.fetchone():
            flash("That email address is already registered. Please use a different email.", "danger")
            return redirect(url_for('admin.view_voters'))
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

                                              
         
                                              

@admin_bp.route("/results")
@admin_required
def view_results():
    college_id = get_admin_college_id()
    election_id = request.args.get('election_id', type=int)
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    if college_id is not None:
        cursor.execute("SELECT id, title FROM elections WHERE status IN ('active', 'completed') AND (college_id=%s OR college_id IS NULL) ORDER BY created_at DESC", (college_id,))
    else:
        cursor.execute("SELECT id, title FROM elections WHERE status IN ('active', 'completed') ORDER BY created_at DESC")
    elections = cursor.fetchall()
    
    # Auto-select the first (latest) election if none specified
    if not election_id and elections:
        election_id = elections[0]["id"]
    
    selected_election = None
    results = []
    total_votes = 0
    total_voters_voted = 0
    total_eligible_voters = 0
    total_voters_not_voted = 0
    voters_voted = []
    voters_not_voted = []
    
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

            election_college_id = selected_election.get('college_id')
            if election_college_id:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM users
                    WHERE role='voter' AND is_approved=1 AND is_active=1
                    AND college_id=%s
                """, (election_college_id,))
            else:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM users
                    WHERE role='voter' AND is_approved=1 AND is_active=1
                """)
            total_eligible_voters = cursor.fetchone()['total'] or 0
            total_voters_not_voted = max(0, total_eligible_voters - total_voters_voted)

            # Fetch list of voters who DID vote
            cursor.execute("""
                SELECT DISTINCT
                    u.id,
                    CONCAT(COALESCE(u.firstname,''), ' ', COALESCE(u.middlename,''), ' ', COALESCE(u.surname,'')) AS full_name,
                    u.email,
                    u.student_id
                FROM users u
                INNER JOIN votes v ON v.voter_id = u.id
                WHERE v.election_id = %s AND u.role = 'voter'
                ORDER BY u.surname, u.firstname
            """, (election_id,))
            voters_voted = [
                {**v, 'full_name': ' '.join(v['full_name'].split())}
                for v in cursor.fetchall()
            ]

            # Fetch list of eligible voters who did NOT vote
            if election_college_id:
                cursor.execute("""
                    SELECT
                        u.id,
                        CONCAT(COALESCE(u.firstname,''), ' ', COALESCE(u.middlename,''), ' ', COALESCE(u.surname,'')) AS full_name,
                        u.email,
                        u.student_id
                    FROM users u
                    WHERE u.role = 'voter'
                      AND u.is_approved = 1
                      AND u.is_active = 1
                      AND u.college_id = %s
                      AND u.id NOT IN (
                          SELECT DISTINCT voter_id FROM votes WHERE election_id = %s
                      )
                    ORDER BY u.surname, u.firstname
                """, (election_college_id, election_id))
            else:
                cursor.execute("""
                    SELECT
                        u.id,
                        CONCAT(COALESCE(u.firstname,''), ' ', COALESCE(u.middlename,''), ' ', COALESCE(u.surname,'')) AS full_name,
                        u.email,
                        u.student_id
                    FROM users u
                    WHERE u.role = 'voter'
                      AND u.is_approved = 1
                      AND u.is_active = 1
                      AND u.id NOT IN (
                          SELECT DISTINCT voter_id FROM votes WHERE election_id = %s
                      )
                    ORDER BY u.surname, u.firstname
                """, (election_id,))
            voters_not_voted = [
                {**v, 'full_name': ' '.join(v['full_name'].split())}
                for v in cursor.fetchall()
            ]
    
    cursor.close()
    conn.close()
    
    return render_template('results.html', elections=elections, election_id=election_id,
                         selected_election=selected_election, results=results,
                         total_votes=total_votes, total_voters_voted=total_voters_voted,
                         total_eligible_voters=total_eligible_voters,
                         total_voters_not_voted=total_voters_not_voted,
                         voters_voted=voters_voted,
                         voters_not_voted=voters_not_voted)

@admin_bp.route("/logs")
@admin_required
def view_logs():
    college_id = get_admin_college_id()
    search = request.args.get('search', '').strip()
    action_filter = request.args.get('action_filter', '').strip() or None
    action_types = ['login', 'logout', 'vote_cast']

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT l.id, l.action, l.details, l.created_at, l.ip_address,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        WHERE u.role='voter' AND u.college_id=%s
    """
    params = [college_id]

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


                                              
                   
                                              

from flask import jsonify
import math

@admin_bp.route("/api/notifications")
@admin_required
def api_notifications():
    """Return recent important system log events as notifications for the admin's college voters."""
    college_id = get_admin_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT l.id, l.action, l.details, l.created_at,
               CONCAT(COALESCE(u.firstname, ''), ' ', COALESCE(u.surname, '')) AS user_name
        FROM system_logs l
        LEFT JOIN users u ON l.user_id = u.id
        WHERE u.role='voter' AND u.college_id=%s
        ORDER BY l.created_at DESC
        LIMIT 15
    """, (college_id,))
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
                                              
from werkzeug.security import check_password_hash, generate_password_hash

@admin_bp.route("/profile")
@admin_required
def view_profile():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.firstname, u.middlename, u.surname, u.email,
               u.student_id, u.role, u.created_at, u.college_id,
               c.name AS college_name
        FROM users u
        LEFT JOIN colleges c ON u.college_id = c.id
        WHERE u.id = %s
    """, (session['user_id'],))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if not admin:
        flash('Profile not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    pw_error_restore = session.pop("admin_pw_error_restore", None)

    return render_template('profile.html', admin=admin, pw_error_restore=pw_error_restore)


@admin_bp.route("/profile/update", methods=["POST"])
@admin_required
def update_profile():
    form_type = request.form.get('form_type', '')
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    if form_type == 'info':
        firstname = request.form.get('firstname', '').strip()
        middlename = request.form.get('middlename', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()

        if not firstname or not surname or not email:
            flash('First name, surname, and email are required.', 'danger')
        else:
            try:
                cursor.execute("""
                    UPDATE users SET firstname=%s, middlename=%s, surname=%s, email=%s
                    WHERE id=%s
                """, (firstname, middlename or None, surname, email, session['user_id']))
                conn.commit()
                                     
                full = f"{firstname} {middlename} {surname}".replace('  ', ' ').strip()
                session['fullname'] = full
                flash('Profile updated successfully.', 'success')
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'danger')

    elif form_type == 'password':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

                            
        cursor.execute("SELECT password FROM users WHERE id=%s", (session['user_id'],))
        row = cursor.fetchone()

        if not row:
            flash('User not found.', 'danger')
        elif not check_password_hash(row['password'], current_password):
            flash('Current password is incorrect.', 'danger')
            session["admin_pw_error_restore"] = {
                "current_password": current_password,
                "new_password": new_password,
                "confirm_password": confirm_password,
            }
        elif len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        else:
            try:
                hashed = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, session['user_id']))
                conn.commit()
                flash('Password updated successfully.', 'success')
            except Exception as e:
                flash(f'Error updating password: {str(e)}', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('admin.view_profile'))