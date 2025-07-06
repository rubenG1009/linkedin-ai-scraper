import psycopg
from typing import Optional, Dict

def test_connection():
    try:
        # Try to connect to the database
        conn = psycopg.connect(
            dbname="my_project",
            user="postgres",
            password="test",
            host="localhost",
            port="5432",
            sslmode="disable"
        )
        print("Successfully connected to the database!")
        
        # Try to execute a simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"Query result: {result}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    test_connection()
