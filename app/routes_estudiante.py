from fastapi import APIRouter, Request, Form, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import get_pool

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def inicio_sesion(request: Request):
    # Si ya tiene el carnet en la sesión, redirigir al dashboard
    if request.session.get("estudiante_carnet"):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="estudiante/login.html", context={"request": request})

@router.post("/login")
async def login_post(request: Request, carnet: str = Form(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verificar si el estudiante existe
        estudiante = await conn.fetchrow("SELECT id, nombre, apellido, grupo_id FROM estudiante WHERE carnet = $1", carnet)
        
        if estudiante:
            # Guardamos la info clave en la sesión
            request.session["estudiante_id"] = estudiante["id"]
            request.session["estudiante_carnet"] = carnet
            request.session["grupo_id"] = estudiante["grupo_id"]
            request.session["estudiante_nombre"] = f"{estudiante['nombre']} {estudiante['apellido']}"
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        else:
            return templates.TemplateResponse(request=request, name="estudiante/login.html", context={
                "request": request, 
                "error": "Carnet no encontrado. ¿Ya te registraste?"
            })

@router.get("/registro", response_class=HTMLResponse)
async def registro(request: Request):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Cargar los grupos para el select
        grupos = await conn.fetch("SELECT id, codigo_grupo FROM grupo ORDER BY codigo_grupo")
    return templates.TemplateResponse(request=request, name="estudiante/registro.html", context={"request": request, "grupos": grupos})

@router.post("/registro")
async def registro_post(
    request: Request,
    nombre: str = Form(...),
    apellido: str = Form(...),
    carnet: str = Form(...),
    grupo_id: int = Form(...)
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            # Intentar registrar al alumno
            await conn.execute(
                "INSERT INTO estudiante (nombre, apellido, carnet, grupo_id) VALUES ($1, $2, $3, $4)",
                nombre, apellido, carnet, grupo_id
            )
            # Iniciar sesión automáticamente tras registro exitoso
            estudiante = await conn.fetchrow("SELECT id FROM estudiante WHERE carnet = $1", carnet)
            request.session["estudiante_id"] = estudiante["id"]
            request.session["estudiante_carnet"] = carnet
            request.session["grupo_id"] = grupo_id
            request.session["estudiante_nombre"] = f"{nombre} {apellido}"
            
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        except Exception as e:
            # Probablemente el carnet ya existe (violación de restricción UNIQUE)
            grupos = await conn.fetch("SELECT id, codigo_grupo FROM grupo ORDER BY codigo_grupo")
            return templates.TemplateResponse(request=request, name="estudiante/registro.html", context={
                "request": request,
                "grupos": grupos,
                "error": "Ese carnet ya está registrado."
            })

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Validar sesión
    estudiante_id = request.session.get("estudiante_id")
    grupo_id = request.session.get("grupo_id")
    
    if not estudiante_id:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # 1. Verificar si hay un periodo activo
        periodo_activo = await conn.fetchrow(
            "SELECT id, fecha_fin FROM periodo_votacion WHERE estado = true AND fecha_fin >= NOW() ORDER BY id DESC LIMIT 1"
        )
        
        if not periodo_activo:
            return templates.TemplateResponse(request=request, name="estudiante/dashboard.html", context={
                "request": request,
                "nombre": request.session.get("estudiante_nombre"),
                "error": "No hay ningún periodo de votación activo en este momento."
            })

        # 2. Cargar los profesores asignados al grupo del estudiante
        # Hacemos JOIN para traer solo los profesores que enseñan al grupo_id del estudiante
        query_profesores = """
            SELECT p.id, p.nombre, p.apellido, p.materias 
            FROM profesor p
            JOIN profesor_grupo pg ON p.id = pg.profesor_id
            WHERE pg.grupo_id = $1 AND p.estado = true
        """
        profesores = await conn.fetch(query_profesores, grupo_id)
        
        # 3. Ver por cuáles profesores YA votó en este periodo para ocultarlos/marcarlos
        votos_emitidos = await conn.fetch(
            "SELECT profesor_id FROM voto WHERE estudiante_id = $1 AND periodo_id = $2",
            estudiante_id, periodo_activo["id"]
        )
        profesores_votados = [v["profesor_id"] for v in votos_emitidos]

    return templates.TemplateResponse(request=request, name="estudiante/dashboard.html", context={
        "request": request,
        "nombre": request.session.get("estudiante_nombre"),
        "profesores": profesores,
        "profesores_votados": profesores_votados,
        "periodo": periodo_activo
    })

@router.get("/votar/{profesor_id}", response_class=HTMLResponse)
async def formulario_votacion(request: Request, profesor_id: int):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Cargar info del profesor
        profesor = await conn.fetchrow("SELECT id, nombre, apellido, materias FROM profesor WHERE id = $1", profesor_id)
        if not profesor:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            
    return templates.TemplateResponse(request=request, name="estudiante/votacion.html", context={
        "request": request,
        "profesor": profesor
    })

@router.post("/votar/{profesor_id}")
async def guardar_voto(
    request: Request,
    profesor_id: int,
    aspecto_1: int = Form(...), aspecto_2: int = Form(...),
    aspecto_3: int = Form(...), aspecto_4: int = Form(...),
    aspecto_5: int = Form(...), aspecto_6: int = Form(...),
    aspecto_7: int = Form(...), aspecto_8: int = Form(...),
    aspecto_9: int = Form(...), aspecto_10: int = Form(...)
):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Validar periodo activo
        periodo = await conn.fetchrow("SELECT id FROM periodo_votacion WHERE estado = true AND fecha_fin >= NOW() ORDER BY id DESC LIMIT 1")
        if not periodo:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

        try:
            # Guardar el voto. Si el estudiante ya votó por este profe en este periodo, lanzará error de restricción UNIQUE.
            await conn.execute("""
                INSERT INTO voto (estudiante_id, profesor_id, periodo_id,
                    aspecto_1_dominio_tema, aspecto_2_puntualidad, aspecto_3_claridad_explicacion,
                    aspecto_4_recursos_didacticos, aspecto_5_resolucion_dudas, aspecto_6_evaluacion_justa,
                    aspecto_7_fomento_participacion, aspecto_8_trato_respetuoso, aspecto_9_organizacion_clase,
                    aspecto_10_cumplimiento_temario)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, estudiante_id, profesor_id, periodo["id"],
            aspecto_1, aspecto_2, aspecto_3, aspecto_4, aspecto_5,
            aspecto_6, aspecto_7, aspecto_8, aspecto_9, aspecto_10)
        except Exception as e:
            # El estudiante intentó votar dos veces
            pass

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
