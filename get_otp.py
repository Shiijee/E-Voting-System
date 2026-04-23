from app import create_app

app = create_app()
conn = app.config['get_db_connection']()
cur = conn.cursor(dictionary=True)

# Get the latest OTP for our test voter
cur.execute("""
    SELECT o.*, u.student_id, u.firstname 
    FROM otps o
    JOIN users u ON o.user_id = u.id
    WHERE u.student_id = '241-1-1234'
    ORDER BY o.created_at DESC
    LIMIT 1
""")
otp_record = cur.fetchone()
if otp_record:
    print(f"Latest OTP for 241-1-1234: {otp_record['otp_code']}")
    print(f"Expires at: {otp_record['expires_at']}")
    print(f"Purpose: {otp_record['purpose']}")
else:
    print("No OTP found in database")

conn.close()
