import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='evoting_db'
)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, student_id, role, firstname, surname FROM users WHERE role IN ('admin', 'superadmin')")
results = cursor.fetchall()
print('Admin/Superadmin users:')
for user in results:
    print(f'ID: {user["id"]}, Student ID: {user["student_id"]}, Role: {user["role"]}, Name: {user["firstname"]} {user["surname"]}')
cursor.close()
conn.close()