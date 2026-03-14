from flask import (
    Blueprint,
    render_template,
    request,
)

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin/static',
)


@admin_bp.route("/login")
def login():
    return render_template('login.html')


@admin_bp.route("/")
def root():
    return render_template('dashboard.html')


@admin_bp.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')


@admin_bp.route("/elections")
def view_elections():
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/new")
def create_election():
    return render_template('election_form.html', action='add', form_data={})


@admin_bp.route("/elections/<int:election_id>/edit")
def edit_election(election_id):
    return render_template('election_form.html', action='edit', election={}, form_data={})


@admin_bp.route("/elections/<int:election_id>/activate")
def activate_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/<int:election_id>/deactivate")
def deactivate_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/<int:election_id>/delete")
def delete_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/positions")
def view_positions():
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/new")
def create_position():
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/<int:position_id>/edit")
def edit_position(position_id):
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/<int:position_id>/delete")
def delete_position(position_id):
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/candidates")
def view_candidates():
    return render_template('candidates.html', candidates=[], elections=[], positions=[])


@admin_bp.route("/candidates/new")
def create_candidate():
    return render_template('candidate_form.html', action='add', form_data={}, elections=[], positions=[])


@admin_bp.route("/candidates/<int:candidate_id>/edit")
def edit_candidate(candidate_id):
    return render_template('candidate_form.html', action='edit', candidate={}, form_data={}, elections=[], positions=[])


@admin_bp.route("/candidates/<int:candidate_id>/delete")
def delete_candidate(candidate_id):
    return render_template('candidates.html', candidates=[], elections=[], positions=[])


@admin_bp.route("/voters")
def view_voters():
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/approve")
def approve_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/reject")
def reject_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/reset-password")
def reset_voter_password(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/delete")
def delete_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/results")
def view_results():
    election_id = request.args.get('election_id', type=int)
    return render_template(
        'results.html',
        elections=[],
        election_id=election_id,
        selected_election=None,
        results=[],
        total_votes=0,
        total_voters_voted=0,
    )


@admin_bp.route("/logs")
def view_logs():
    return render_template(
        'logs.html',
        logs=[],
        search='',
        action_filter=None,
        action_types=[],
    )
