# app/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.langgraph_parser import parse_message
from app.crud import list_cases, update_cases, delete_cases
from app.config import OPENAI_API_KEY
from openai import OpenAI
import os

router = APIRouter()
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Request model
class ChatRequest(BaseModel):
    message: str

# Response model
class ChatResponse(BaseModel):
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = []
    errors: Optional[List[str]] = []

@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat_endpoint(payload: ChatRequest):
    try:
        user_message = payload.message.strip()

        # Parse message using LangGraph
        parsed_result = parse_message(user_message)
        intent = parsed_result.get("intent")
        entities = parsed_result.get("entities", {})

        if intent == "create_case":
            # En este caso especial, el title es único y se hace una inserción manual (no SQL dinámico).
            from app.db import get_connection
            conn = get_connection()
            cur = conn.cursor()

            title = entities.get("title")
            if not title:
                return ChatResponse(
                    success=False,
                    message="No se proporcionó un título para el caso.",
                    errors=["Campo 'title' requerido"]
                )

            # Check for duplicate title
            cur.execute("SELECT * FROM Cases WHERE title = %s", (title,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return ChatResponse(
                    success=False,
                    message=f"Ya existe un caso con el título ‘{title}’.",
                    errors=[]
                )

            status_ = entities.get("status", "")
            description = entities.get("description", "")
            attorney = entities.get("attorney", "")

            insert_query = """
                INSERT INTO Cases (title, status, description, attorney)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, status, description, attorney, created_at;
            """
            cur.execute(insert_query, (title, status_, description, attorney))
            new_case = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return ChatResponse(
                success=True,
                message=f"Nuevo caso creado: {new_case[1]}, estado {new_case[2]}.",
                data=[{
                    "id": new_case[0],
                    "title": new_case[1],
                    "status": new_case[2],
                    "description": new_case[3],
                    "attorney": new_case[4],
                    "created_at": new_case[5].isoformat()
                }],
                errors=[]
            )

        elif intent == "read_cases":
            result = list_cases(user_message)
            return ChatResponse(**result)

        elif intent == "update_case":
            result = update_cases(user_message)
            return ChatResponse(**result)

        elif intent == "delete_case":
            result = delete_cases(user_message)
            return ChatResponse(**result)

        elif intent == "general_question":
            completion = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Responde con precisión y claridad."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_tokens=300
            )
            text = completion.choices[0].message.content.strip()
            return ChatResponse(
                success=True,
                message=text,
                data=[],
                errors=[]
            )

        else:
            return ChatResponse(
                success=False,
                message="No se pudo identificar la intención del mensaje.",
                data=[],
                errors=["Intención desconocida"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )