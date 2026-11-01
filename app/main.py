from contextlib import asynccontextmanager
import logging

import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import LeadRequest
from .database import create_pool, init_db, save_lead


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    pool = await create_pool()

    # 2. Сохраняем пул, чтобы обработчики могли его использовать
    app.state.db_pool = pool

    try:
        await init_db(pool)
        # 4. Здесь FastAPI начинает принимать запросы
        yield

    finally:
        # 5. Закрываем пул при остановке приложения
        await pool.close()


app = FastAPI(lifespan=lifespan)


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
async def main_root():
    return {"message": "Кварта API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/lead", status_code=201)
async def create_lead(lead: LeadRequest):
    # Получаем пул, созданный при запуске приложения
    pool: asyncpg.Pool = app.state.db_pool

    try:
        # Сохраняем заявку в PostgreSQL
        lead_id = await save_lead(
            pool,
            lead.model_dump(),
        )

    except asyncpg.PostgresError:
        logger.exception("Ошибка PostgreSQL при сохранении заявки")
        raise HTTPException(
            status_code=500,
            detail="Не удалось отправить заявку. Попробуйте позже.",
        )

    except OSError:
        logger.exception("Ошибка подключения к базе данных")
        raise HTTPException(
            status_code=500,
            detail="Не удалось отправить заявку. Попробуйте позже.",
        )

    # Номер уже использовался в течение последних 10 минут
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
