from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from Voxify.Authentication.routes import login_required, admin_required

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/admin/static',
)


@admin_bp.route("/login")
def login():
    # If already logged in as admin, go straight to dashboard
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))


@admin_bp.route("/")
@admin_required
def root():
    return redirect(url_for('admin.dashboard'))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template('dashboard.html')


@admin_bp.route("/elections")
@admin_required
def view_elections():
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/new")
@admin_required
def create_election():
    return render_template('election_form.html', action='add', form_data={})


@admin_bp.route("/elections/<int:election_id>/edit")
@admin_required
def edit_election(election_id):
    return render_template('election_form.html', action='edit', election={}, form_data={})


@admin_bp.route("/elections/<int:election_id>/activate")
@admin_required
def activate_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/<int:election_id>/deactivate")
@admin_required
def deactivate_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/elections/<int:election_id>/delete")
@admin_required
def delete_election(election_id):
    return render_template('elections.html', elections=[])


@admin_bp.route("/positions")
@admin_required
def view_positions():
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/new")
@admin_required
def create_position():
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/<int:position_id>/edit")
@admin_required
def edit_position(position_id):
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/positions/<int:position_id>/delete")
@admin_required
def delete_position(position_id):
    return render_template('positions.html', positions=[], elections=[])


@admin_bp.route("/candidates")
@admin_required
def view_candidates():
    return render_template('candidates.html', candidates=[], elections=[], positions=[])


@admin_bp.route("/candidates/new")
@admin_required
def create_candidate():
    return render_template('candidate_form.html', action='add', form_data={}, elections=[], positions=[])


@admin_bp.route("/candidates/<int:candidate_id>/edit")
@admin_required
def edit_candidate(candidate_id):
    return render_template('candidate_form.html', action='edit', candidate={}, form_data={}, elections=[], positions=[])


@admin_bp.route("/candidates/<int:candidate_id>/delete")
@admin_required
def delete_candidate(candidate_id):
    return render_template('candidates.html', candidates=[], elections=[], positions=[])


@admin_bp.route("/voters")
@admin_required
def view_voters():
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/approve")
@admin_required
def approve_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/reject")
@admin_required
def reject_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/reset-password")
@admin_required
def reset_voter_password(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/voters/<int:voter_id>/delete")
@admin_required
def delete_voter(voter_id):
    return render_template('voters.html', voters=[])


@admin_bp.route("/results")
@admin_required
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
@admin_required
def view_logs():
    return render_template(
        'logs.html',
        logs=[],
        search='',
        action_filter=None,
        action_types=[],
    )