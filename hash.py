# save as fix_admins.py
from werkzeug.security import generate_password_hash
import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="evoting_db"
)
cursor = conn.cursor()

# Update Super Admin (password: superadmin123)
superadmin_hash = generate_password_hash("superadmin123")
cursor.execute("""
    UPDATE users 
    SET password = %s 
    WHERE role = 'superadmin' AND username = 'superadmin'
""", (superadmin_hash,))

# Update Admin (password: admin123)
admin_hash = generate_password_hash("admin123")
cursor.execute("""
    UPDATE users 
    SET password = %s 
    WHERE role = 'admin' AND username = 'admin'
""", (admin_hash,))

conn.commit()

print("Updated passwords:")
print(f"  Super Admin - Username: superadmin, Password: superadmin123")
print(f"  Admin - Username: admin, Password: admin123")
print(f"\nHash values:")
print(f"  Superadmin: {superadmin_hash}")
print(f"  Admin: {admin_hash}")

# Verify the updates
cursor.execute("SELECT username, role, LEFT(password, 50) as pwd_preview FROM users WHERE role IN ('admin', 'superadmin')")
users = cursor.fetchall()
print("\nVerified users:")
for user in users:
    print(f"  Username: {user[0]}, Role: {user[1]}")
    print(f"    Hash preview: {user[2]}...")

cursor.close()
conn.close()