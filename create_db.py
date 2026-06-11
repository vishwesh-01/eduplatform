"""
create_db.py — Creates the edu_platform PostgreSQL database if it doesn't exist.
Run once: python create_db.py
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="2305",
    database="postgres"
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname = 'edu_platform'")
if cur.fetchone():
    print("Database 'edu_platform' already exists.")
else:
    cur.execute("CREATE DATABASE edu_platform")
    print("Database 'edu_platform' created successfully.")

cur.close()
conn.close()
