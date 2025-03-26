# app/crud.py

from typing import Dict, Any, List
from openai import OpenAI
from app.db import get_db_connection
from app.config import OPENAI_API_KEY

# Initialize the OpenAI API client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def create_case(title: str, status: str, description: str, attorney: str) -> Dict[str, Any]:
    """
    Create a new case in the database with the provided details.
    Args:
        title (str): The title of the case.
        status (str): The status of the case.
        description (str): The description of the case.
        attorney (str): The attorney assigned to the case.
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.        
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verifies if a case with the same title already exists
        cur.execute("SELECT id FROM Cases WHERE title = %s", (title,))
        if cur.fetchone():
            return {
                "success": False,
                "message": f"Ya existe un caso con el título '{title}'.",
                "data": [],
                "errors": []
            }

        # Insert the new case into the database
        insert_query = """
            INSERT INTO Cases (title, status, description, attorney)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, status, description, attorney, created_at;
        """
        cur.execute(insert_query, (title, status, description, attorney))
        new_case = cur.fetchone()
        conn.commit()

        # If the case was successfully created, return the details
        return {
            "success": True,
            "message": f"Nuevo caso creado: {new_case[1]}, estado {new_case[2]}.",
            "data": [{
                "id": new_case[0],
                "title": new_case[1],
                "status": new_case[2],
                "description": new_case[3],
                "attorney": new_case[4],
                "created_at": new_case[5].isoformat()
            }],
            "errors": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Error al crear el caso.",
            "data": [],
            "errors": [str(e)]
        }
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


def execute_dynamic_query(prompt: str, query_type: str) -> Dict[str, Any]:
    """
    Generate a SQL query dynamically using OpenAI based on the user prompt and execute the generated query on the 'Cases' table.
    Args:
        prompt (str): The user instruction for generating the SQL query.
        query_type (str): The type of SQL query to generate (SELECT, UPDATE, DELETE).
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.        
    """
    system_prompt = (
        "You are a PostgreSQL query generator for a legal case management system. "
        "The table is called 'Cases' and has the following columns:\n"
        "id (serial primary key), title (text), status (text), description (text), attorney (text), created_at (timestamp).\n"
        f"Generate a single SQL {query_type.upper()} query without explanations or formatting.\n"
        "Respond ONLY with the SQL query.\n\n"
        f"User instruction: {prompt}"
    )
    # Generate the SQL query using OpenAI
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0
    )
    # Extract the SQL query from the completion and execute it
    sql_query = completion.choices[0].message.content.strip()
    return run_sql_query(sql_query, query_type)


def run_sql_query(query: str, query_type: str) -> Dict[str, Any]:
    """
    Excecutes the SQL query on the 'Cases' table. Can be a SELECT, UPDATE, or DELETE query.
    Args:
        query (str): The SQL query to execute.
        query_type (str): The type of SQL query (SELECT, UPDATE, DELETE).
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
    Exception:
        Exception: Any exception raised during the execution of the SQL query.                    
    """
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
    """
    Send a user instruction to generate and execute a SELECT query on the 'Cases' table.
    Args:
        user_instruction (str): The user instruction for generating the SELECT query.
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
    """
    return execute_dynamic_query(user_instruction, "select")


def update_cases(user_instruction: str) -> Dict[str, Any]:
    """
    Send a user instruction to generate and execute an UPDATE query on the 'Cases' table.
    Args:
        user_instruction (str): The user instruction for generating the UPDATE query.
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
    """
    return execute_dynamic_query(user_instruction, "update")


def delete_cases(user_instruction: str) -> Dict[str, Any]:
    """
    Send a user instruction to generate and execute a DELETE query on the 'Cases' table.
    Args:
        user_instruction (str): The user instruction for generating the DELETE query.
    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
    """
    return execute_dynamic_query(user_instruction, "delete")
