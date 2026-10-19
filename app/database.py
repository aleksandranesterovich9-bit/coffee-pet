import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Путь к файлу базы данных kvarta.db в корне проекта
DB_PATH = Path(__file__).resolve().parent.parent / "kvarta.db"


def init_db():
    """Создаёт таблицу заявок, если её ещё нет."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                interest TEXT NOT NULL,
                comment TEXT,
                utm_source TEXT,
                utm_campaign TEXT,
                utm_content TEXT,
                landing_page TEXT,
                created_at TEXT NOT NULL
            )
        """)


def save_lead(data: dict) -> int | None:
    """
    Сохраняет заявку в базу данных.

    Возвращает ID заявки при успехе.
    Возвращает None, если с этого номера
    уже поступала заявка за последние 10 минут.
    """
    phone = data["phone"]

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(minutes=10)).isoformat()
    created_at = now.isoformat()

    connection = sqlite3.connect(DB_PATH, timeout=10)

    try:
        # Блокируем начало записи, чтобы уменьшить риск
        # создания двух заявок при двойном нажатии.
        connection.execute("BEGIN IMMEDIATE")

        duplicate = connection.execute(
            """
            SELECT id
            FROM leads
            WHERE phone = ?
              AND created_at >= ?
            LIMIT 1
            """,
            (phone, cutoff),
        ).fetchone()

        if duplicate:
            connection.rollback()
            return None

        cursor = connection.execute(
            """
            INSERT INTO leads (
                name,
                phone,
                interest,
                comment,
                utm_source,
                utm_campaign,
                utm_content,
                landing_page,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                phone,
                data["interest"],
                data.get("comment"),
                data.get("utm_source"),
                data.get("utm_campaign"),
                data.get("utm_content"),
                data.get("landing_page"),
                created_at,
            ),
        )

        lead_id = cursor.lastrowid
        connection.commit()

        return lead_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

init_db()
