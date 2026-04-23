from app import create_app

app = create_app()
conn = app.config['get_db_connection']()
cur = conn.cursor(dictionary=True)

# Get all candidates
cur.execute("""
    SELECT c.id, c.firstname, c.surname, c.photo, p.title as position_title, p.id as position_id
    FROM candidates c
    JOIN positions p ON c.position_id = p.id
""")
candidates = [dict(row) for row in cur.fetchall()]
print("All candidates:")
for c in candidates:
    photo_status = f"Photo: {c['photo']}" if c['photo'] else "NO PHOTO"
    print(f"  ID {c['id']}: {c['firstname']} {c['surname']} - {c['position_title']} - {photo_status}")

conn.close()
