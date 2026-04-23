from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
from Voxify.Authentication.routes import voter_required

voter_bp = Blueprint('voter', __name__,
                     template_folder='templates', 
                     static_folder='static',
                     static_url_path='/voter/static')

def get_voter_college_id():
    """Get the college_id of the currently logged-in voter."""
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT college_id FROM users WHERE id=%s", (session['user_id'],))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['college_id'] if result else None

@voter_bp.route("/dashboard")
@voter_required
def dashboard():
    college_id = get_voter_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT e.*, 
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted
        FROM elections e
        WHERE e.status = 'active' AND e.start_date <= NOW() AND e.end_date >= NOW()
        AND e.college_id = %s
        ORDER BY e.end_date ASC
    """, (session['user_id'], college_id))
    active_elections = cursor.fetchall()
    
    cursor.execute("""
        SELECT * FROM elections 
        WHERE status = 'upcoming' AND start_date > NOW() AND college_id = %s
        ORDER BY start_date ASC
    """, (college_id,))
    upcoming_elections = cursor.fetchall()
    
    cursor.execute("""
        SELECT e.*, 
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted
        FROM elections e
        WHERE (e.status = 'completed' OR e.end_date < NOW()) AND e.college_id = %s
        ORDER BY e.end_date DESC
        LIMIT 5
    """, (session['user_id'], college_id))
    past_elections = cursor.fetchall()

    # Get recent votes with candidate info
    cursor.execute("""
        SELECT v.cast_at, e.title as election_title, e.id as election_id,
               p.title as position_title,
               c.firstname, c.surname
        FROM votes v
        JOIN elections e ON v.election_id = e.id
        JOIN positions p ON v.position_id = p.id
        JOIN candidates c ON v.candidate_id = c.id
        WHERE v.voter_id = %s
        ORDER BY v.cast_at DESC
        LIMIT 6
    """, (session['user_id'],))
    recent_votes = cursor.fetchall()

    # Total votes cast by this voter
    cursor.execute("SELECT COUNT(*) as total FROM votes WHERE voter_id=%s", (session['user_id'],))
    total_votes_cast = cursor.fetchone()['total']

    # Get college name
    college = None
    if college_id:
        cursor.execute("SELECT name FROM colleges WHERE id=%s", (college_id,))
        college = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template("voter_dashboard.html", 
                         active_elections=active_elections,
                         upcoming_elections=upcoming_elections,
                         past_elections=past_elections,
                         recent_votes=recent_votes,
                         total_votes_cast=total_votes_cast,
                         college=college)

@voter_bp.route("/elections")
@voter_required
def elections():
    college_id = get_voter_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted,
               (SELECT COUNT(*) FROM positions p WHERE p.election_id = e.id) as position_count
        FROM elections e
        WHERE e.college_id = %s
        ORDER BY e.created_at DESC
    """, (session['user_id'], college_id))
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("voter_elections.html", elections=elections)

@voter_bp.route("/elections/<int:election_id>/ballot", methods=["GET", "POST"])
@voter_required
def ballot(election_id):
    college_id = get_voter_college_id()
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    # Check election exists, is active, AND belongs to voter's college
    cursor.execute("SELECT * FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
    election = cursor.fetchone()
    
    if not election:
        flash("Election not found or not available for your college.", "error")
        return redirect(url_for('voter.elections'))
    
    if election['status'] != 'active':
        flash("This election is not active.", "warning")
        return redirect(url_for('voter.elections'))
    
    cursor.execute("SELECT COUNT(*) as voted FROM votes WHERE election_id=%s AND voter_id=%s", 
                  (election_id, session['user_id']))
    if cursor.fetchone()['voted'] > 0:
        flash("You have already voted in this election.", "warning")
        return redirect(url_for('voter.results', election_id=election_id))
    
    if request.method == "POST":
        votes_cast = 0
        for key, value in request.form.items():
            if key.startswith('position_'):
                position_id = int(key.split('_')[1])
                candidate_id = int(value)
                cursor.execute("""
                    INSERT INTO votes (voter_id, election_id, position_id, candidate_id) 
                    VALUES (%s, %s, %s, %s)
                """, (session['user_id'], election_id, position_id, candidate_id))
                votes_cast += 1
        conn.commit()
        flash(f"Your vote has been cast successfully! You voted for {votes_cast} position(s).", "success")
        cursor.close()
        conn.close()
        return redirect(url_for('voter.results', election_id=election_id))
    
    cursor.execute("""
        SELECT p.*, 
               (SELECT COUNT(*) FROM candidates c WHERE c.position_id = p.id) as candidate_count
        FROM positions p
        WHERE p.election_id = %s
        ORDER BY p.display_order
    """, (election_id,))
    positions = cursor.fetchall()
    
    for position in positions:
        cursor.execute("""
            SELECT * FROM candidates 
            WHERE position_id = %s AND status = 'approved'
            ORDER BY surname
        """, (position['id'],))
        position['candidates'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template("voter_ballot.html", election=election, positions=positions)

@voter_bp.route("/my-votes")
@voter_required
def my_votes():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.*, e.title as election_title, p.title as position_title, 
               c.firstname, c.surname, c.student_id
        FROM votes v
        JOIN elections e ON v.election_id = e.id
        JOIN positions p ON v.position_id = p.id
        JOIN candidates c ON v.candidate_id = c.id
        WHERE v.voter_id = %s
        ORDER BY v.cast_at DESC
    """, (session['user_id'],))
    votes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("voter_my_votes.html", votes=votes)

@voter_bp.route("/results")
@voter_required
def results():
    college_id = get_voter_college_id()
    election_id = request.args.get('election_id', type=int)
    
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    
    # Only show elections from voter's college
    cursor.execute("""
        SELECT id, title FROM elections 
        WHERE status != 'upcoming' AND college_id = %s
        ORDER BY created_at DESC
    """, (college_id,))
    elections = cursor.fetchall()
    
    selected_election = None
    results = []
    total_votes = 0
    user_voted = False
    
    if election_id:
        cursor.execute("SELECT * FROM elections WHERE id=%s AND college_id=%s", (election_id, college_id))
        selected_election = cursor.fetchone()
        
        if selected_election:
            cursor.execute("SELECT COUNT(*) as voted FROM votes WHERE election_id=%s AND voter_id=%s", 
                          (election_id, session['user_id']))
            user_voted = cursor.fetchone()['voted'] > 0

            cursor.execute("""
                SELECT
                    p.id AS position_id,
                    p.title AS position_title,
                    c.id AS candidate_id,
                    c.firstname, c.middlename, c.surname, c.student_id,
                    COALESCE(c.photo, '') AS photo,
                    COUNT(v.id) AS vote_count
                FROM positions p
                LEFT JOIN candidates c ON c.position_id = p.id
                LEFT JOIN votes v ON v.candidate_id = c.id AND v.election_id = %s
                WHERE p.election_id = %s
                GROUP BY p.id, p.title, c.id, c.firstname, c.middlename, c.surname, c.student_id, c.photo
                ORDER BY p.display_order, vote_count DESC
            """, (election_id, election_id))
            rows = cursor.fetchall()

            positions = {}
            for row in rows:
                pos = positions.setdefault(row['position_id'], {
                    'position': {'title': row['position_title']},
                    'candidates': [],
                    'total_votes': 0
                })
                if row['candidate_id'] is not None:
                    full_name = ' '.join(filter(None, [row['firstname'], row['middlename'], row['surname']])).strip()
                    pos['candidates'].append({
                        'vote_count': row['vote_count'] or 0,
                        'candidate': {
                            'full_name': full_name or 'Unknown',
                            'student_id': row['student_id'],
                            'photo': row['photo']
                        }
                    })
                    pos['total_votes'] += row['vote_count'] or 0

            for pos in positions.values():
                for cand in pos['candidates']:
                    cand['percentage'] = round((cand['vote_count'] / pos['total_votes']) * 100, 1) if pos['total_votes'] > 0 else 0.0

            results = list(positions.values())

            cursor.execute("SELECT COUNT(DISTINCT voter_id) as total FROM votes WHERE election_id=%s", (election_id,))
            total_votes = cursor.fetchone()['total'] or 0
    
    cursor.close()
    conn.close()
    
    return render_template("voter_results.html", elections=elections, election_id=election_id,
                         selected_election=selected_election, results=results, 
                         total_votes=total_votes, user_voted=user_voted)

@voter_bp.route("/profile")
@voter_required
def profile():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.student_id, u.firstname, u.middlename, u.surname,
               u.email, u.created_at, u.is_approved, u.is_active,
               c.name as college_name
        FROM users u
        LEFT JOIN colleges c ON u.college_id = c.id
        WHERE u.id=%s
    """, (session['user_id'],))
    voter = cursor.fetchone()

    # Compute full name and counts
    if voter:
        voter['full_name'] = ' '.join(filter(None, [voter['firstname'], voter['middlename'], voter['surname']])).strip()

    cursor.execute("SELECT COUNT(*) as total FROM votes WHERE voter_id=%s", (session['user_id'],))
    total_votes = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(DISTINCT election_id) as total FROM votes WHERE voter_id=%s", (session['user_id'],))
    elections_participated = cursor.fetchone()['total']

    cursor.close()
    conn.close()
    return render_template("voter_profile.html", voter=voter,
                           total_votes=total_votes,
                           elections_participated=elections_participated)