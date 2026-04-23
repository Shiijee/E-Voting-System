from app import create_app
from werkzeug.security import generate_password_hash

app = create_app()
conn = app.config['get_db_connection']()
cur = conn.cursor()

# Set password for Chicken soup (ID 241-1-1234)
password = "test123"
hashed_password = generate_password_hash(password)

cur.execute(
    "UPDATE users SET password=%s WHERE student_id=%s",
    (hashed_password, "241-1-1234")
)
conn.commit()
print(f"Set password for voter 241-1-1234 to: {password}")
cur.close()
conn.close()
