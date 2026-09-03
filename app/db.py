import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Pool perezoso: se crea en la primera consulta, no al arrancar.
    statement_cache_size=0 es obligatorio con el pooler de Supabase (pgbouncer en
    modo transaction): sin esto asyncpg falla con DuplicatePreparedStatementError.
    """
    global pool
    if pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL no está configurada en .env")
        pool = await asyncpg.create_pool(
            DATABASE_URL, statement_cache_size=0, min_size=1, max_size=5,
            # search_path explícito: el pooler comparte conexiones entre aplicaciones y
            # un SET ajeno podría dejarnos apuntando a otro esquema.
            server_settings={"search_path": "public"},
        )
    return pool


async def close_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def periodo_activo(conn):
    """Periodo abierto ahora mismo. Lo usan estudiantes y admin, para no descuadrarse."""
    return await conn.fetchrow(
        "SELECT id, fecha_inicio, fecha_fin FROM periodo_votacion "
        "WHERE estado = true AND fecha_fin >= NOW() ORDER BY id DESC LIMIT 1"
    )
