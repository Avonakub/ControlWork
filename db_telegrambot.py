import psycopg2
import datetime


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
            telegram_id BIGINT UNIQUE NOT NULL,
            registered TIMESTAMP NOT NULL DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS user_actions (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT REFERENCES users(telegram_id),
            action_user TEXT NOT NULL,
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
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
        print(f"User {username} with ID {telegram_id} registered at {datetime.datetime.now()}!")
        print("✅ Logs saved")


def save_user_action(conn, telegram_id, action_user, user_message=None, bot_response=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO user_actions (telegram_id, action_user, user_message, bot_response)
            VALUES (%s, %s, %s, %s)
        """, (telegram_id, action_user, user_message, bot_response))
        conn.commit()
        print(f"Action '{action_user}' saved for user {telegram_id}")


def main():
    with connect_db() as conn:
        print("Connected to database successfully!")
        initialize_db(conn)
        print("🟢 Tables created")

main()
