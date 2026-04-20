import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='', database='evoting_db')
cursor = conn.cursor()
cursor.execute('DESCRIBE candidates')
for row in cursor.fetchall():
    print(row)
cursor.close()
conn.close()
