from flask import Flask
import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="evoting_db"
    )
    return connection

def create_app():
    app = Flask(__name__, static_folder=None)
    app.secret_key = '04a5b29e6c18f7f5035af7fa603b3fc1'  # Change this to a random secret key

    # Register modules
    from Voxify.Admin.routes import admin_bp
    from Voxify.Voter.routes import voter_bp
    from Voxify.Authentication.routes import auth_bp
    from Voxify.SuperAdmin.routes import superadmin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(voter_bp, url_prefix="/voter")
    app.register_blueprint(superadmin_bp, url_prefix="/superadmin")

    # make db accessible in other files
    app.config["get_db_connection"] = get_db_connection

    return app
