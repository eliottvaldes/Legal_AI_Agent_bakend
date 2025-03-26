# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as chat_router
from app.db import create_cases_table

# Define the FastAPI app 
app = FastAPI(title="Legal Case Chat API")

# define CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create table when the server starts
@app.on_event("startup")
def startup():
    create_cases_table()

# Register routes from the chat_router
app.include_router(chat_router)