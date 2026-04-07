from werkzeug.security import generate_password_hash
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="evoting_db"
)

cursor = conn.cursor()

# Update current database users to known login credentials.
# Voter passwords here are reset to their student IDs so they can log in immediately.
updates = [
    ('SUPER001', 'superadmin', 'superadmin123'),
    ('ADMIN001', 'admin', 'admin123'),
    ('20240001', '20240001', '20240001'),
    ('241-0001', '241-0001', '241-0001'),
]

for student_id, username, password in updates:
    hashed_password = generate_password_hash(password)
    cursor.execute(
        """UPDATE users SET username=%s, password=%s WHERE student_id=%s""",
        (username, hashed_password, student_id)
    )
    print(f"Updated {student_id}: username={username}, password={password}")

conn.commit()

cursor.execute("SELECT id, student_id, username, role, LEFT(password, 50) FROM users ORDER BY id")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()
