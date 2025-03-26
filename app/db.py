# app/db.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Return a connection to the PostgreSQL database using environment variables.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", 5432)
    )


def create_cases_table():
    """
    # Create the "Cases" table if it does not exist and define a uniqueness constraint on the 'title' field.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Cases (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        description TEXT,
        attorney TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()