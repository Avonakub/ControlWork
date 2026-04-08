import psycopg2


def connect_db():
    conn = psycopg2.connect(
        dbname="db_telegrambot",
        user="postgres",
        password="12345",
        host="localhost",
        port="5432"
    )
    return conn


def initialize_db(conn):
    with conn.cursor() as cur: # курсор
        query = """CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            telegram_id BIGINT UNIQUE NOT NULL
        )
        """
        cur.execute(query)
        conn.commit()


def register_user(conn,username=None, telegram_id=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (username, telegram_id) 
            VALUES (%s, %s)
            ON CONFLICT (telegram_id) DO NOTHING
        """, (username, telegram_id))
        conn.commit()
        print(f"User {username} with ID {telegram_id} registered!")


def main():
    with connect_db() as conn:
        print("Connected to database successfully!")
        initialize_db(conn)
        print("🟢 Tables created")

main()
