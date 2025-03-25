# app/db.py

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Retorna una conexión a la base de datos PostgreSQL utilizando las variables de entorno.
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
    Crea la tabla "Cases" si no existe y define una restricción de unicidad en el campo 'title'.
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