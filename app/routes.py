from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import authenticate

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    redirect_url = authenticate(username, password)
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    else:
        return PlainTextResponse("Usuario o contraseña incorrectos", status_code=401)


@router.get("/seleccionatuprofesor", response_class=HTMLResponse)
async def read_seleccionatuprofesor(request: Request):
    return templates.TemplateResponse(request=request, name="selectProfesor.html", context={})


@router.post("/seleccionatuprofesor")
async def seleccionar_profesor(request: Request, maestro: str = Form(...)):
    if not maestro:
        return templates.TemplateResponse(
            request=request,
            name="selectProfesor.html",
            context={"error": "Selecciona un profesor"}
        )
    return templates.TemplateResponse(
        request=request,
        name="calification_plataform.html",
        context={"maestro": maestro}
    )


@router.get("/administrador", response_class=HTMLResponse)
async def read_administrador(request: Request):
    return templates.TemplateResponse(request=request, name="administradorMain.html", context={})


@router.get("/gestionProfesores", response_class=HTMLResponse)
async def read_gestion_profesores(request: Request):
    return templates.TemplateResponse(request=request, name="gestionProfesores.html", context={})


@router.get("/gestionProfesoresInformacion", response_class=HTMLResponse)
async def read_gestion_profesores_informacion(request: Request):
    return templates.TemplateResponse(request=request, name="gestionProfesoresInformacion.html", context={})


@router.get("/centroEstadistico", response_class=HTMLResponse)
async def read_centro_estadistico(request: Request):
    return templates.TemplateResponse(request=request, name="centroEstadistico.html", context={})


@router.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request):
    return templates.TemplateResponse(request=request, name="configuracion.html", context={})


@router.get("/calificaElProfesor", response_class=HTMLResponse)
async def read_calificaElProfesor(request: Request):
    return templates.TemplateResponse(request=request, name="calification_plataform.html", context={"maestro": ""})


@router.post("/calificaElProfesor")
async def enviar_calificacion(
    request: Request,
    maestro: str = Form(...),
    explicationsTopics: str = Form(...),
    actitudinal: str = Form(...),
    classActivity: str = Form(...)
):
    if not explicationsTopics or not actitudinal or not classActivity:
        return templates.TemplateResponse(
            request=request,
            name="calification_plataform.html",
            context={"maestro": maestro, "error": "Selecciona una nota para cada casilla"}
        )
    return RedirectResponse(url="/Agradecimiento", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/Agradecimiento", response_class=HTMLResponse)
async def read_agradecimiento(request: Request):
    return templates.TemplateResponse(request=request, name="certificado.html", context={})
