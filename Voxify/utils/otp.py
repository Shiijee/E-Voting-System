import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import session, current_app, request
import hashlib
import secrets

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3
TRUSTED_DEVICE_EXPIRY_DAYS = 7

def generate_otp():
    """Generate a secure 6-digit numeric OTP"""
    return ''.join(random.choices('0123456789', k=OTP_LENGTH))

def hash_otp(otp):
    """Hash the OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()

def send_otp_email(email, otp):
    """Send OTP via Gmail SMTP"""
    try:
        # Get SMTP settings from app config
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')

        # Debug: Check if credentials exist
        print(f"[OTP DEBUG] SMTP_USERNAME: {smtp_username}")
        print(f"[OTP DEBUG] SMTP_PASSWORD set: {bool(smtp_password and smtp_password != 'your-app-password')}")

        if not all([smtp_username, smtp_password]):
            raise ValueError("SMTP credentials not configured")
        
        if smtp_password == 'your-app-password':
            raise ValueError("SMTP_PASSWORD is still default placeholder. Set environment variable SMTP_PASSWORD with actual Gmail App Password.")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = 'Your OTP for Voxify E-Voting System'

        body = f"""
        Your One-Time Password (OTP) for Voxify is: {otp}

        This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.

        If you didn't request this OTP, please ignore this email.

        Best regards,
        Voxify Team
        """
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()

        return True
    except Exception as e:
        import traceback
        print(f"[OTP ERROR] Email sending failed: {e}")
        traceback.print_exc()
        return False

def store_otp_in_session(otp, purpose, user_data=None):
    """Store OTP temporarily in session with expiration and attempt counter"""
    hashed_otp = hash_otp(otp)
    expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    session[f'otp_{purpose}'] = {
        'hashed_otp': hashed_otp,
        'expiry': expiry_time.isoformat(),
        'attempts': 0
    }

    # Store user data for signup and login
    if user_data:
        session[f'user_data_{purpose}'] = user_data

def verify_otp_from_session(otp, purpose):
    """Verify OTP from session, check expiry and attempts"""
    otp_key = f'otp_{purpose}'
    if otp_key not in session:
        return False, "No OTP found"

    otp_data = session[otp_key]
    hashed_input = hash_otp(otp)

    # Check attempts
    if otp_data['attempts'] >= MAX_ATTEMPTS:
        clear_otp_from_session(purpose)
        return False, "Maximum attempts exceeded"

    # Check expiry
    expiry_time = datetime.fromisoformat(otp_data['expiry'])
    if datetime.now() > expiry_time:
        clear_otp_from_session(purpose)
        return False, "OTP has expired"

    # Check OTP
    if hashed_input != otp_data['hashed_otp']:
        otp_data['attempts'] += 1
        session[otp_key] = otp_data
        return False, f"Invalid OTP. {MAX_ATTEMPTS - otp_data['attempts']} attempts remaining"

    # Success - only clear OTP data, NOT user_data (needed in next step)
    otp_key = f'otp_{purpose}'
    if otp_key in session:
        del session[otp_key]
    
    return True, "OTP verified successfully"

def clear_otp_from_session(purpose):
    """Clear OTP data from session"""
    otp_key = f'otp_{purpose}'
    user_data_key = f'user_data_{purpose}'

    if otp_key in session:
        del session[otp_key]
    if user_data_key in session:
        del session[user_data_key]

def generate_trusted_device_token():
    """Generate a secure token for trusted device"""
    return secrets.token_urlsafe(32)

def set_trusted_device(user_id, response):
    """Set trusted device cookie for 7 days"""
    token = generate_trusted_device_token()
    expiry = datetime.now() + timedelta(days=TRUSTED_DEVICE_EXPIRY_DAYS)

    # Store token in database (you might want to create a trusted_devices table)
    # For now, we'll store in session as well, but ideally use DB
    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()

    # Assuming you have a trusted_devices table:
    # CREATE TABLE trusted_devices (user_id INT, token VARCHAR(255), expiry DATETIME, PRIMARY KEY (user_id))

    try:
        cursor.execute("""
            INSERT INTO trusted_devices (user_id, token, expiry)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE token=%s, expiry=%s
        """, (user_id, token, expiry, token, expiry))
        conn.commit()
    except Exception as e:
        print(f"Error storing trusted device: {e}")
        # Fallback to session if table doesn't exist
        session['trusted_device'] = {'token': token, 'expiry': expiry.isoformat()}
    finally:
        cursor.close()
        conn.close()

    # Set secure cookie
    response.set_cookie(
        'trusted_device',
        token,
        max_age=TRUSTED_DEVICE_EXPIRY_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite='Strict'
    )

def check_trusted_device(user_id):
    """Check if device is trusted"""
    token = request.cookies.get('trusted_device')
    if not token:
        return False

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT expiry FROM trusted_devices
            WHERE user_id=%s AND token=%s
        """, (user_id, token))
        result = cursor.fetchone()

        if result:
            expiry = result['expiry']
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry)
            if datetime.now() < expiry:
                return True
            else:
                # Expired, remove from DB
                cursor.execute("DELETE FROM trusted_devices WHERE user_id=%s AND token=%s", (user_id, token))
                conn.commit()
    except Exception as e:
        print(f"Error checking trusted device: {e}")
        # Fallback to session
        if 'trusted_device' in session:
            device_data = session['trusted_device']
            expiry = datetime.fromisoformat(device_data['expiry'])
            if datetime.now() < expiry and device_data['token'] == token:
                return True
    finally:
        cursor.close()
        conn.close()

    return False