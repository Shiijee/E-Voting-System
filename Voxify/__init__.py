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
    app = Flask(__name__)

    # Register modules
    from Voxify.Admin.routes import admin_bp
    from Voxify.Voter.routes import voter_bp
    from Voxify.Authentication.routes import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(voter_bp, url_prefix="/voter")

    # make db accessible in other files
    app.config["get_db_connection"] = get_db_connection

    return app