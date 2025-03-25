# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as chat_router
from app.db import create_cases_table

app = FastAPI(title="Legal Case Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tabla al iniciar el servidor
@app.on_event("startup")
def startup():
    create_cases_table()

# Registrar rutas
app.include_router(chat_router)