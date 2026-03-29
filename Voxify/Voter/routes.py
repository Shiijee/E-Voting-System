from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from Voxify.Authentication.routes import voter_required

voter_bp = Blueprint('voter', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/voter/static')


@voter_bp.route("/dashboard")
@voter_required
def dashboard():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted
        FROM elections e
        WHERE e.status = 'active' AND e.start_date <= NOW() AND e.end_date >= NOW()
        ORDER BY e.end_date ASC
    """, (session['user_id'],))
    active_elections = cursor.fetchall()

    cursor.execute("""
        SELECT * FROM elections
        WHERE status = 'upcoming' AND start_date > NOW()
        ORDER BY start_date ASC
    """)
    upcoming_elections = cursor.fetchall()

    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted
        FROM elections e
        WHERE e.status = 'completed' OR e.end_date < NOW()
        ORDER BY e.end_date DESC
        LIMIT 5
    """, (session['user_id'],))
    past_elections = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("voter_dashboard.html",
                           active_elections=active_elections,
                           upcoming_elections=upcoming_elections,
                           past_elections=past_elections)


@voter_bp.route("/elections")
@voter_required
def elections():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM votes v WHERE v.election_id = e.id AND v.voter_id = %s) as has_voted
        FROM elections e
        ORDER BY e.created_at DESC
    """, (session['user_id'],))
    elections = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("voter_elections.html", elections=elections)


@voter_bp.route("/elections/<int:election_id>/ballot", methods=["GET", "POST"])
@voter_required
def ballot(election_id):
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
    election = cursor.fetchone()

    if not election:
        flash("Election not found.", "error")
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
    election_id = request.args.get('election_id', type=int)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM elections WHERE status != 'upcoming' ORDER BY created_at DESC")
    elections = cursor.fetchall()

    selected_election = None
    results = []
    total_votes = 0
    user_voted = False

    if election_id:
        cursor.execute("SELECT * FROM elections WHERE id=%s", (election_id,))
        selected_election = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as voted FROM votes WHERE election_id=%s AND voter_id=%s",
                       (election_id, session['user_id']))
        user_voted = cursor.fetchone()['voted'] > 0

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

    return render_template("voter_results.html", elections=elections, election_id=election_id,
                           selected_election=selected_election, results=results,
                           total_votes=total_votes, user_voted=user_voted)


@voter_bp.route("/profile")
@voter_required
def profile():
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, student_id, firstname, middlename, surname, username, created_at FROM users WHERE id=%s",
                   (session['user_id'],))
    voter = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("voter_profile.html", voter=voter)
