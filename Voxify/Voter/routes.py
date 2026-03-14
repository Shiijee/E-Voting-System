from flask import Blueprint, render_template, request

voter_bp = Blueprint(
    'voter',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/voter/static',
)


@voter_bp.route("/dashboard")
def dashboard():
    return render_template("voter_dashboard.html")


@voter_bp.route("/elections")
def elections():
    return render_template("voter_elections.html", elections=[])


@voter_bp.route("/elections/<int:election_id>/ballot")
def ballot(election_id):
    return render_template("voter_ballot.html", election={}, positions=[])


@voter_bp.route("/my-votes")
def my_votes():
    return render_template("voter_my_votes.html", votes=[])


@voter_bp.route("/results")
def results():
    election_id = request.args.get('election_id', type=int)
    return render_template(
        "voter_results.html",
        elections=[],
        election_id=election_id,
        selected_election=None,
        results=[],
        total_votes=0,
    )


@voter_bp.route("/profile")
def profile():
    return render_template("voter_profile.html", voter=None)
