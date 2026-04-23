from app import create_app

app = create_app()
conn = app.config['get_db_connection']()
cur = conn.cursor(dictionary=True)
cur.execute('SELECT student_id, firstname, surname FROM users WHERE role="voter" AND is_approved=1 LIMIT 3')
voters = [dict(row) for row in cur.fetchall()]
print("Available voters:")
for v in voters:
    print(f"  {v['student_id']} - {v['firstname']} {v['surname']}")
conn.close()
