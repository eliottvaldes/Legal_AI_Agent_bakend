# app/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.langgraph_parser import parse_message
from app.crud import list_cases, update_cases, delete_cases, create_case
from app.config import OPENAI_API_KEY
from openai import OpenAI

router = APIRouter()
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class ChatRequest(BaseModel):
    """
    Modelo de datos para la solicitud POST de /chat
    """
    message: str


class ChatResponse(BaseModel):
    """
    Modelo de datos para la respuesta de /chat
    """
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = []
    errors: Optional[List[str]] = []


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat_endpoint(payload: ChatRequest):
    """
    Punto de entrada principal para manejar las solicitudes de chat.
    Analiza la intención del mensaje, extrae entidades y realiza la acción correspondiente.
    """
    try:
        user_message = payload.message.strip()

        # Procesa la intención y entidades del mensaje
        parsed_result = parse_message(user_message)
        intent = parsed_result.get("intent")
        entities = parsed_result.get("entities", {})
        
        print("*" * 50)
        print(f'Parsed result: {parsed_result}')
        print(f'User message: {user_message}')
        print(f'Intent: {intent}')
        print(f'Entities: {entities}')
        print("*" * 50)

        if intent == "create_case":
            # Se maneja la creación de un nuevo caso
            title = entities.get("title", "").strip()
            if not title:
                return ChatResponse(
                    success=False,
                    message="No se proporcionó un título para el caso.",
                    errors=["Campo 'title' requerido"]
                )

            status_ = entities.get("status", "").strip()
            description = entities.get("description", "").strip()
            attorney = entities.get("attorney", "").strip()

            result = create_case(title, status_, description, attorney)
            return ChatResponse(**result)

        elif intent == "read_cases" or intent == "'read_cases'":
            # Lectura de casos vía SQL dinámico generado por OpenAI
            result = list_cases(user_message)
            return ChatResponse(**result)

        elif intent == "update_case" or intent == "'update_case'":
            # Actualización de casos vía SQL dinámico generado por OpenAI
            result = update_cases(user_message)
            return ChatResponse(**result)

        elif intent == "delete_case" or intent == "'delete_case'":
            # Eliminación de casos vía SQL dinámico generado por OpenAI
            result = delete_cases(user_message)
            return ChatResponse(**result)

        elif intent == "general_question" or intent == "'general_question'":
            
            print("Entro a general_question")            
            
            # Consulta general a ChatGPT
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Responde con precisión y claridad."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                max_tokens=300
            )
            print(f"completion: {completion}")
            text = completion.choices[0].message.content.strip()
            print(f"text: {text}")
            return ChatResponse(
                success=True,
                message=text,
                data=[],
                errors=[]
            )

        else:
            
            print(f'Intent no reconocida: {intent}')
            print(f'Parsed result: {parsed_result}')            
            
            # Si no se detecta una intención reconocida
            return ChatResponse(
                success=False,
                message="No se pudo identificar la intención del mensaje.",
                data=[],
                errors=["Intención desconocida"]
            )

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
