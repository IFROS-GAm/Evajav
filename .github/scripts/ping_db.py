"""
Consulta mínima contra la base de datos para que Supabase no la considere inactiva.

El plan gratuito de Supabase pausa un proyecto tras ~7 días sin actividad, y
reactivarlo es manual: si eso pasa en plena semana de evaluación, la aplicación
queda fuera de servicio. Este script se ejecuta desde GitHub Actions cada pocos
días y basta para que el proyecto cuente como vivo.
"""
import asyncio
import os
import sys

import asyncpg

URL = os.getenv("DATABASE_URL")
if not URL:
    sys.exit("Falta el secreto DATABASE_URL en el repositorio "
             "(Settings → Secrets and variables → Actions).")


async def main():
    # statement_cache_size=0 por el pooler de Supabase (pgbouncer en modo transaction).
    conexion = await asyncpg.connect(URL, statement_cache_size=0, timeout=30)
    try:
        version = await conexion.fetchval("SELECT current_setting('server_version')")
        ahora = await conexion.fetchval("SELECT now()")
        print(f"Base viva. PostgreSQL {version}, hora del servidor {ahora}.")
    finally:
        await conexion.close()


asyncio.run(main())
