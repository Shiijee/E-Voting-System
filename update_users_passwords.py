from werkzeug.security import generate_password_hash
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="evoting_db"
)

cursor = conn.cursor()

# Change student_id and new_password to whichever account you're locked out of
student_id = "241-1-0003"   # <-- change this to your student_id
new_password = "Voter@1234" # <-- change this to your new password

hashed_password = generate_password_hash(new_password)
cursor.execute(
    "UPDATE users SET password=%s WHERE student_id=%s",
    (hashed_password, student_id)
)
conn.commit()
print(f"Password reset for {student_id}. You can now log in with: {new_password}")

cursor.close()
conn.close()