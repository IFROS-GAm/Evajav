import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Cargamos las variables de entorno
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️ ADVERTENCIA: DATABASE_URL no está configurada en .env")

pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    """
    Retorna el pool de conexiones a PostgreSQL.
    Esto permite reutilizar conexiones y hacer la app más rápida.
    """
    global pool
    if pool is None:
        if not DATABASE_URL:
             raise RuntimeError("DATABASE_URL is not set")
        # Iniciar el pool de asyncpg (ideal para Supabase)
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def init_db():
    """
    Función para inicializar la conexión al arrancar el servidor.
    No vamos a crear tablas aquí, porque usaremos database.md en Supabase directamente.
    """
    await get_pool()
    print("OK: Conexión a la base de datos establecida.")

async def close_db():
    """
    Cierra el pool de conexiones al apagar el servidor.
    """
    global pool
    if pool is not None:
        await pool.close()
        print("STOP: Conexión a la base de datos cerrada.")
