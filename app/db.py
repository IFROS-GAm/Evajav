import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("Database_URL") 

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

pool: asyncpg.Pool | None = None


<<<<<<< HEAD
async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool


async def init_db():
    p = await get_pool()
    async with p.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiante (
                id SERIAL PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
=======
def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS esrudiante (
                    id SERIAL PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS maestro (
                    id SERIAL PRIMARY KEY,
                    nota TEXT NOT NULL,
                    name TEXT NOT NULL,
                    grado TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
>>>>>>> c26b636a3ff9b4817884dc49469ec3efb5b36ec0
            )
            """)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS maestro (
                id SERIAL PRIMARY KEY,
                nota TEXT,
                name TEXT NOT NULL,
                grado TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
