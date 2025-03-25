# app/crud.py


from typing import Dict, Any
from openai import OpenAI
from app.db import get_db_connection
from app.config import OPENAI_API_KEY

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def execute_dynamic_query(prompt: str, query_type: str) -> Dict[str, Any]:
    system_prompt = (
        f"You are a PostgreSQL query generator for a legal case management system. "
        f"The table is called 'Cases' and has the following columns:\n"
        f"id (serial primary key), title (text), status (text), description (text), attorney (text), created_at (timestamp).\n"
        f"Generate a single SQL {query_type.upper()} query without explanations or formatting.\n"
        f"Respond ONLY with the SQL query.\n\n"
        f"User instruction: {prompt}"
    )

    completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0
    )

    sql_query = completion.choices[0].message.content.strip()
    return run_sql_query(sql_query, query_type)


def run_sql_query(query: str, query_type: str) -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if query_type.lower() == "select":
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in rows]
            message = "Casos existentes." if results else "No se encontraron casos."
            return {
                "success": True,
                "message": message,
                "data": results,
                "errors": []
            }

        elif query_type.lower() == "update":
            cur.execute(query)
            affected = cur.rowcount
            conn.commit()
            return {
                "success": True,
                "message": f"Se actualizaron {affected} caso(s) correctamente.",
                "data": [],
                "errors": []
            }

        elif query_type.lower() == "delete":
            cur.execute(query)
            affected = cur.rowcount
            conn.commit()
            return {
                "success": True,
                "message": f"Se eliminaron {affected} caso(s) correctamente.",
                "data": [],
                "errors": []
            }

        else:
            return {
                "success": False,
                "message": "Tipo de operación SQL no soportado.",
                "data": [],
                "errors": [f"Unsupported query type: {query_type}"]
            }

    except Exception as e:
        return {
            "success": False,
            "message": "Error al ejecutar la operación.",
            "data": [],
            "errors": [str(e)]
        }

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


def list_cases(user_instruction: str) -> Dict[str, Any]:
    return execute_dynamic_query(user_instruction, "select")


def update_cases(user_instruction: str) -> Dict[str, Any]:
    return execute_dynamic_query(user_instruction, "update")


def delete_cases(user_instruction: str) -> Dict[str, Any]:
    return execute_dynamic_query(user_instruction, "delete")