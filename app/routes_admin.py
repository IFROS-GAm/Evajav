import os
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.db import get_pool

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

def is_admin(request: Request) -> bool:
    return request.session.get("is_admin") is True

@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    if is_admin(request):
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"request": request})

@router.post("/login")
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="admin/login.html", context={
        "request": request, 
        "error": "Credenciales incorrectas."
    })

@router.get("/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo_activo = await conn.fetchrow("SELECT * FROM periodo_votacion WHERE estado = true ORDER BY id DESC LIMIT 1")
        total_votos = await conn.fetchval("SELECT count(*) FROM voto")
        total_estudiantes = await conn.fetchval("SELECT count(*) FROM estudiante")
        
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context={
        "request": request,
        "periodo_activo": periodo_activo,
        "total_votos": total_votos,
        "total_estudiantes": total_estudiantes
    })

@router.post("/periodo/nuevo")
async def admin_nuevo_periodo(request: Request, fecha_fin: str = Form(...)):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Desactivar periodos anteriores
        await conn.execute("UPDATE periodo_votacion SET estado = false")
        # Insertar nuevo (Nota: requiere castear fecha_fin en PostgreSQL)
        await conn.execute("INSERT INTO periodo_votacion (fecha_fin) VALUES ($1::timestamp)", fecha_fin)
        
    return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/reportes", response_class=HTMLResponse)
async def admin_reportes(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verificar si hay algún periodo cerrado del cual sacar promedios
        periodos_cerrados = await conn.fetch("SELECT id, fecha_inicio, fecha_fin FROM periodo_votacion WHERE estado = false OR fecha_fin < NOW() ORDER BY id DESC")
        
        # Para simplificar, generamos el reporte del último periodo cerrado (o activo si queremos ver progreso global, pero la regla dice "solo accesibles después de cerrada la votación")
        # Asumiremos que reportes solo muestra info del periodo cerrado más reciente para ser simples
        if not periodos_cerrados:
            return templates.TemplateResponse(request=request, name="admin/reportes.html", context={
                "request": request,
                "error": "No hay periodos de votación cerrados todavía."
            })
            
        periodo_id = periodos_cerrados[0]["id"]
        
        # Consulta de promedios agrupados de forma anonimizada
        query_promedios = """
            SELECT 
                p.nombre, p.apellido,
                COUNT(v.id) as cantidad_votos,
                AVG(v.aspecto_1_dominio_tema) as a1,
                AVG(v.aspecto_2_puntualidad) as a2,
                AVG(v.aspecto_3_claridad_explicacion) as a3,
                AVG(v.aspecto_4_recursos_didacticos) as a4,
                AVG(v.aspecto_5_resolucion_dudas) as a5,
                AVG(v.aspecto_6_evaluacion_justa) as a6,
                AVG(v.aspecto_7_fomento_participacion) as a7,
                AVG(v.aspecto_8_trato_respetuoso) as a8,
                AVG(v.aspecto_9_organizacion_clase) as a9,
                AVG(v.aspecto_10_cumplimiento_temario) as a10
            FROM voto v
            JOIN profesor p ON v.profesor_id = p.id
            WHERE v.periodo_id = $1
            GROUP BY p.id
        """
        resultados = await conn.fetch(query_promedios, periodo_id)
        
    return templates.TemplateResponse(request=request, name="admin/reportes.html", context={
        "request": request,
        "resultados": resultados
    })
