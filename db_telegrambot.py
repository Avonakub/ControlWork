import psycopg2
import Telegram_BOT

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


def main():
    with connect_db() as conn:
        print("Connected to database successfully!")
        initialize_db(conn)
        print("🟢 Tables created")

main()
