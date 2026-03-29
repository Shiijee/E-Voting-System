import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import session, current_app, request
import hashlib
import secrets

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3
TRUSTED_DEVICE_EXPIRY_DAYS = 7


def generate_otp():
    return ''.join(random.choices('0123456789', k=OTP_LENGTH))


def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()


def send_otp_email(email, otp):
    try:
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')

        if not all([smtp_username, smtp_password]):
            raise ValueError("SMTP credentials not configured")

        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = 'Your OTP for Voxify E-Voting System'

        body = f"""Your One-Time Password (OTP) for Voxify is: {otp}

This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this OTP, please ignore this email.

Best regards,
Voxify Team
"""
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def store_otp_in_session(otp, purpose, user_data=None):
    hashed_otp = hash_otp(otp)
    expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    session[f'otp_{purpose}'] = {
        'hashed_otp': hashed_otp,
        'expiry': expiry_time.isoformat(),
        'attempts': 0
    }
    if user_data:
        session[f'user_data_{purpose}'] = user_data


def verify_otp_from_session(otp, purpose):
    otp_key = f'otp_{purpose}'
    if otp_key not in session:
        return False, "No OTP found"

    otp_data = session[otp_key]
    hashed_input = hash_otp(otp)

    if otp_data['attempts'] >= MAX_ATTEMPTS:
        clear_otp_from_session(purpose)
        return False, "Maximum attempts exceeded"

    expiry_time = datetime.fromisoformat(otp_data['expiry'])
    if datetime.now() > expiry_time:
        clear_otp_from_session(purpose)
        return False, "OTP has expired"

    if hashed_input != otp_data['hashed_otp']:
        otp_data['attempts'] += 1
        session[otp_key] = otp_data
        return False, f"Invalid OTP. {MAX_ATTEMPTS - otp_data['attempts']} attempts remaining"

    del session[otp_key]
    return True, "OTP verified successfully"


def clear_otp_from_session(purpose):
    session.pop(f'otp_{purpose}', None)
    session.pop(f'user_data_{purpose}', None)


def generate_trusted_device_token():
    return secrets.token_urlsafe(32)


def set_trusted_device(user_id, response):
    token = generate_trusted_device_token()
    expiry = datetime.now() + timedelta(days=TRUSTED_DEVICE_EXPIRY_DAYS)

    conn = current_app.config["get_db_connection"]()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO trusted_devices (user_id, token, expiry)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE token=%s, expiry=%s
        """, (user_id, token, expiry, token, expiry))
        conn.commit()
    except Exception as e:
        print(f"Error storing trusted device: {e}")
    finally:
        cursor.close()
        conn.close()

    response.set_cookie(
        'trusted_device',
        token,
        max_age=TRUSTED_DEVICE_EXPIRY_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=False,
        samesite='Strict'
    )


def check_trusted_device(user_id):
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
            cursor.execute("DELETE FROM trusted_devices WHERE user_id=%s AND token=%s", (user_id, token))
            conn.commit()
    except Exception as e:
        print(f"Error checking trusted device: {e}")
    finally:
        cursor.close()
        conn.close()

    return False
