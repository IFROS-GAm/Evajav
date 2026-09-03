import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[1]
# Las fechas se guardan en UTC; se muestran y se leen en la hora local del colegio.
ZONA = ZoneInfo(os.getenv("ZONA_HORARIA", "America/Bogota"))
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def fecha(valor, formato: str = "%d/%m/%Y %H:%M") -> str:
    return "—" if valor is None else valor.astimezone(ZONA).strftime(formato)


def leer_fecha(texto: str) -> datetime:
    """Convierte lo que envía un <input type=datetime-local> a fecha con zona."""
    return datetime.fromisoformat(texto).replace(tzinfo=ZONA)


templates.env.filters["fecha"] = fecha
templates.env.filters["dia"] = lambda v: fecha(v, "%d/%m/%Y")


def render(request: Request, name: str, status_code: int = 200, **context):
    """Atajo: mete el mensaje flash y evita repetir request en cada llamada."""
    return templates.TemplateResponse(
        request=request, name=name, status_code=status_code,
        context={"flash": request.session.pop("flash", None), **context},
    )


def redirect(url: str, request: Request = None, flash: str = None):
    """Redirect 303 con mensaje opcional para mostrar en la página destino."""
    if flash and request is not None:
        request.session["flash"] = flash
    return RedirectResponse(url=url, status_code=303)
