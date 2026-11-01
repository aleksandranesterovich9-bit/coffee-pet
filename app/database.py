import asyncpg
import os
from dotenv import load_dotenv

from datetime import datetime, timedelta, timezone

load_dotenv()


async def create_pool() -> asyncpg.Pool:
    from urllib.parse import urlparse, unquote

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL не найдена в .env")

    parsed = urlparse(database_url)

    return await asyncpg.create_pool(
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=parsed.path.lstrip("/"),
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 5432,
    )


async def init_db(pool: asyncpg.Pool) -> None:
    """Создаёт таблицу заявок, если её ещё нет."""
    async with pool.acquire() as connection:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                interest TEXT NOT NULL,
                comment TEXT,
                utm_source TEXT,
                utm_campaign TEXT,
                utm_content TEXT,
                landing_page TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


async def save_lead(pool: asyncpg.Pool, data: dict) -> int | None:
    """
    Сохраняет заявку.

    Возвращает ID при успехе или None,
    если номер уже использовался за последние 10 минут.
    """
    async with pool.acquire() as connection:
        async with connection.transaction():
            # Сериализуем обработку заявок с одним номером.
            await connection.execute(
                """
                SELECT pg_advisory_xact_lock(
                    hashtextextended($1, 0)
                )
                """,
                data["phone"],
            )

            duplicate = await connection.fetchval(
                """
                SELECT id
                FROM leads
                WHERE phone = $1
                  AND created_at >= $2
                LIMIT 1
                """,
                data["phone"],
                datetime.now(timezone.utc) - timedelta(minutes=10),
            )

            if duplicate is not None:
                return None

            lead_id = await connection.fetchval(
                """
                INSERT INTO leads (
                    name, phone, interest, comment,
                    utm_source, utm_campaign, utm_content,
                    landing_page
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                data["name"],
                data["phone"],
                data["interest"],
                data.get("comment"),
                data.get("utm_source"),
                data.get("utm_campaign"),
                data.get("utm_content"),
                data.get("landing_page"),
            )

            return lead_id
