from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()

def create_app():
    app = Flask(__name__)

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'evoting_db'

    mysql.init_app(app)

    # Register modules
    from Voxify.Admin.routes import admin_bp
    from Voxify.Voter.routes import voter_bp
    from Voxify.Authentication.routes import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(voter_bp, url_prefix="/voter")

    return app