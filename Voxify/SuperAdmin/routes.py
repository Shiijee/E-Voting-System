from flask import Blueprint, render_template, request
from Voxify.Authentication.routes import superadmin_required

superadmin_bp = Blueprint(
    'super_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/superadmin/static',
)


@superadmin_bp.route("/")
@superadmin_required
def root():
    return render_template('super_dashboard.html')


@superadmin_bp.route("/dashboard")
@superadmin_required
def dashboard():
    return render_template('super_dashboard.html')


@superadmin_bp.route("/manage-admins")
@superadmin_required
def manage_admins():
    return render_template('manage_admins.html')


@superadmin_bp.route("/system-logs")
@superadmin_required
def system_logs():
    return render_template('system_logs.html')