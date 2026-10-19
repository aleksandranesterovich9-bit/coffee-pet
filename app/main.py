from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import LeadRequest
from .database import save_lead
import sqlite3
import logging

app = FastAPI()

logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def main_root():
    return {"message": "Кварта API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/lead", status_code=201)
def create_lead(lead: LeadRequest):
    try:
        lead_id = save_lead(lead.model_dump())
    except sqlite3.Error:
        logger.exception("Не удалось сохранить заявку")
        raise HTTPException(status_code=500,detail="Не удалось отправить заявку. Попробуйте позже.")

    if lead_id is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Вы уже отправляли заявку с этого номера. "
                "Попробуйте снова через 10 минут."
            ),
        )

    return {
        "message": "Заявка успешно принята",
        "lead_id": lead_id,
    }
