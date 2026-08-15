import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.db import init_db, close_db
from app.routes_estudiante import router as router_estudiante
from app.routes_admin import router as router_admin

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conectarse a Supabase al arrancar
    await init_db()
    yield
    # Cerrar pool al apagar
    await close_db()

app = FastAPI(lifespan=lifespan)

import traceback
from fastapi.responses import JSONResponse
from fastapi import Request
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"message": str(exc)})

# Middleware para sesiones (necesario para guardar login de alumnos y admin)
# NOTA: En un proyecto real, SECRET_KEY debe ser seguro y oculto en .env
secret_key = os.getenv("SECRET_KEY", "secreto_desarrollo_temporal_123")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Montar archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir los endpoints de estudiantes y administrador
app.include_router(router_estudiante)
app.include_router(router_admin)
