import os
import secrets
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from app.db import close_db  # noqa: E402  (después de load_dotenv)
from app.routes_admin import router as router_admin
from app.routes_estudiante import router as router_estudiante
from app.web import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    # No conectamos aquí: el pool es perezoso, así la app arranca aunque la BD esté caída.
    yield
    await close_db()


app = FastAPI(title="Evaluación Docente", lifespan=lifespan, docs_url=None, redoc_url=None)

# SECRET_KEY debe venir de .env. Sin ella se genera una al azar: las sesiones se
# invalidan al reiniciar, pero nadie puede firmar cookies con un valor conocido.
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY") or secrets.token_hex(32),
                   same_site="lax", https_only=os.getenv("HTTPS_ONLY") == "1")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router_estudiante)
app.include_router(router_admin)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.png")


@app.exception_handler(asyncpg.PostgresError)
@app.exception_handler(OSError)
async def base_caida(request: Request, exc: Exception):
    """La base no responde (Supabase pausado, red caída): es un 503, no un fallo del usuario."""
    traceback.print_exc()
    return render(request, "error.html", status_code=503,
                  titulo="Sin conexión con la base de datos",
                  detalle="El sistema no puede consultar los datos en este momento. "
                          "Vuelve a intentarlo en unos minutos.")


@app.exception_handler(Exception)
async def error_interno(request: Request, exc: Exception):
    """El detalle va al log del servidor, nunca al navegador (filtraría datos de la BD)."""
    traceback.print_exc()
    return render(request, "error.html", status_code=500)
