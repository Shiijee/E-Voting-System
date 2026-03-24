from flask import Blueprint, render_template, request

superadmin_bp = Blueprint(
    'super_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/superadmin/static',
)

@superadmin_bp.route("/")
def root():
    return render_template('super_dashboard.html')

@superadmin_bp.route("/dashboard")
def dashboard():
    return render_template('super_dashboard.html')

@superadmin_bp.route("/manage-admins")
def manage_admins():
    return render_template('manage_admins.html')

@superadmin_bp.route("/system-logs")
def system_logs():
    return render_template('system_logs.html')
