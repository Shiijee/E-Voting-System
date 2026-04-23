from app import create_app

app = create_app()
conn = app.config['get_db_connection']()
cur = conn.cursor(dictionary=True)

# Check candidates with photos
cur.execute("""
    SELECT c.id, c.firstname, c.surname, c.photo, p.title as position_title
    FROM candidates c
    JOIN positions p ON c.position_id = p.id
    WHERE c.photo IS NOT NULL AND c.photo != ''
    LIMIT 5
""")
candidates = [dict(row) for row in cur.fetchall()]
print(f"Candidates with photos: {len(candidates)}")
for c in candidates:
    print(f"  {c['firstname']} {c['surname']} - {c['position_title']}: {c['photo']}")

# Check total candidates
cur.execute("SELECT COUNT(*) as total FROM candidates")
total = cur.fetchone()['total']
print(f"\nTotal candidates: {total}")

conn.close()
