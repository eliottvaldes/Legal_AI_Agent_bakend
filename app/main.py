# app/main.py

from fastapi import FastAPI
from app.routes import router as chat_router
from app.db import create_cases_table

app = FastAPI(title="Sistema Legal - Backend")

@app.on_event("startup")
def startup_event():
    """
    Se ejecuta al iniciar la aplicación, creando la tabla "Cases" si no existe.
    """
    create_cases_table()

# Incluimos el router para manejar /chat
app.include_router(chat_router)