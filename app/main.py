# app/main.py
from fastapi import FastAPI
from app.routes import router as chat_router
from app.db import create_cases_table

app = FastAPI(title="Sistema Legal - Backend")

# Execute table creation on application startup event (lifespan)
@app.on_event("startup")
def startup_event():
    create_cases_table()

# Include the router for the POST /chat endpoint
app.include_router(chat_router)
