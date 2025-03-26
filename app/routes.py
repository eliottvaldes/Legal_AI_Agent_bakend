# app/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.langgraph_parser import parse_message
from app.crud import list_cases, update_cases, delete_cases, create_case
from app.config import OPENAI_API_KEY
from openai import OpenAI

# Define the FastAPI router
router = APIRouter()
# Create an instance of the OpenAI API client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    """
    # Data model for POST request to /chat
    """
    message: str

class ChatResponse(BaseModel):
    """
    Data model for the response from /chat
    """
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = []
    errors: Optional[List[str]] = []


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat_endpoint(payload: ChatRequest):
    """
    # Main entry point to handle chat requests.
    Analyses the intent of the message, extracts entities, and performs the corresponding action.
    """
    try:
        user_message = payload.message.strip()

        # Process the intent and entities of the message
        parsed_result = parse_message(user_message)
        intent = parsed_result.get("intent")
        entities = parsed_result.get("entities", {})

        # Depending on the intent, perform the corresponding action
        if intent == "create_case":
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
            result = list_cases(user_message)
            return ChatResponse(**result)

        elif intent == "update_case" or intent == "'update_case'":
            result = update_cases(user_message)
            return ChatResponse(**result)

        elif intent == "delete_case" or intent == "'delete_case'":
            result = delete_cases(user_message)
            return ChatResponse(**result)

        elif intent == "general_question" or intent == "'general_question'":
            
            # Use the OpenAI API to generate a response for general questions            
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
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

            # If no recognized intent is detected return an error message
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
