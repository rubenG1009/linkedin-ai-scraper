import psycopg2

def test_connection():
    try:
        conn = psycopg2.connect(
            dbname="my_project",
            user="postgres",
            password="test",
            host="localhost",
            port="5432"
        )
        print("Connection successful!")
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_connection()
