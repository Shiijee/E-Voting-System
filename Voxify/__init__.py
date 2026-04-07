from flask import Flask
import mysql.connector
from mysql.connector import Error
import os

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="evoting_db"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_trusted_devices_table():
    """Create trusted_devices table if it doesn't exist"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trusted_devices (
                    user_id INT PRIMARY KEY,
                    token VARCHAR(255) NOT NULL,
                    expiry DATETIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_token (user_id, token),
                    INDEX idx_expiry (expiry)
                )
            """)
            conn.commit()
            print("Trusted devices table ready")
        except Error as e:
            print(f"Error creating trusted_devices table: {e}")
        finally:
            cursor.close()
            conn.close()

def create_app():
    app = Flask(__name__, static_folder=None)
    
    # Use a fixed secret key for development
    app.secret_key = '04a5b29e6c18f7f5035af7fa603b3fc1'

    # Session configuration
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_NAME'] = 'evoting_session'  # Custom session name

    # SMTP Configuration for OTP emails
    app.config['SMTP_SERVER'] = 'smtp.gmail.com'
    app.config['SMTP_PORT'] = 587
    app.config['SMTP_USERNAME'] = os.getenv('SMTP_USERNAME', 'voxify.otpsender@gmail.com')
    app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD', 'gfse pldo qfls izfy')

    from Voxify.Admin.routes import admin_bp
    from Voxify.Voter.routes import voter_bp
    from Voxify.Authentication.routes import auth_bp
    from Voxify.SuperAdmin.routes import superadmin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(voter_bp, url_prefix="/voter")
    app.register_blueprint(superadmin_bp, url_prefix="/superadmin")

    app.config["get_db_connection"] = get_db_connection

    # Create trusted_devices table on startup
    with app.app_context():
        create_trusted_devices_table()

    return app