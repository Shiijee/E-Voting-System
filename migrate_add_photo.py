import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(host='localhost', user='root', password='', database='evoting_db')
    cursor = conn.cursor()
    
    # Check if photo column exists
    cursor.execute("SHOW COLUMNS FROM candidates LIKE 'photo'")
    result = cursor.fetchone()
    
    if result is None:
        # Add photo column if it doesn't exist
        cursor.execute("ALTER TABLE candidates ADD COLUMN photo VARCHAR(255) NULL DEFAULT NULL")
        conn.commit()
        print("Photo column added to candidates table successfully!")
    else:
        print("Photo column already exists in candidates table.")
    
    cursor.close()
    conn.close()
except Error as e:
    print(f"Error: {e}")
