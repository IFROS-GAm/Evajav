from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.db import get_pool, periodo_activo
from app.web import redirect, render

router = APIRouter()

# Columnas de la tabla voto, en el mismo orden que aspecto_1..aspecto_10 del formulario
COLUMNAS_VOTO = [
    "aspecto_1_dominio_tema", "aspecto_2_puntualidad", "aspecto_3_claridad_explicacion",
    "aspecto_4_recursos_didacticos", "aspecto_5_resolucion_dudas", "aspecto_6_evaluacion_justa",
    "aspecto_7_fomento_participacion", "aspecto_8_trato_respetuoso",
    "aspecto_9_organizacion_clase", "aspecto_10_cumplimiento_temario",
]
INSERT_VOTO = (
    "INSERT INTO voto (estudiante_id, profesor_id, periodo_id, "
    + ", ".join(COLUMNAS_VOTO)
    + ") VALUES (" + ", ".join(f"${i}" for i in range(1, 14)) + ")"
)

SQL_PROFESOR_DEL_GRUPO = """
    SELECT p.id, p.nombre, p.apellido, p.materias
    FROM profesor p
    JOIN profesor_grupo pg ON pg.profesor_id = p.id
    WHERE p.estado = true AND pg.grupo_id = $1
"""


@router.get("/", response_class=HTMLResponse)
async def inicio_sesion(request: Request):
    if request.session.get("estudiante_id"):
        return redirect("/dashboard")
    return render(request, "estudiante/login.html")


@router.post("/login")
async def login_post(request: Request, carnet: str = Form(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        estudiante = await conn.fetchrow(
            "SELECT id, nombre, apellido, grupo_id FROM estudiante WHERE carnet = $1", carnet.strip()
        )
    if not estudiante:
        return render(request, "estudiante/login.html", error="Carnet no encontrado. ¿Ya te registraste?")
    iniciar_sesion(request, estudiante["id"], carnet.strip(), estudiante["grupo_id"],
                   f"{estudiante['nombre']} {estudiante['apellido']}")
    return redirect("/dashboard")


@router.get("/registro", response_class=HTMLResponse)
async def registro(request: Request):
    pool = await get_pool()
    async with pool.acquire() as conn:
        grupos = await conn.fetch("SELECT id, codigo_grupo FROM grupo ORDER BY codigo_grupo")
    return render(request, "estudiante/registro.html", grupos=grupos)


@router.post("/registro")
async def registro_post(
    request: Request,
    nombre: str = Form(...), apellido: str = Form(...),
    carnet: str = Form(...), grupo_id: int = Form(...),
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            estudiante_id = await conn.fetchval(
                "INSERT INTO estudiante (nombre, apellido, carnet, grupo_id) "
                "VALUES ($1, $2, $3, $4) RETURNING id",
                nombre.strip(), apellido.strip(), carnet.strip(), grupo_id,
            )
        except UniqueViolationError:
            grupos = await conn.fetch("SELECT id, codigo_grupo FROM grupo ORDER BY codigo_grupo")
            return render(request, "estudiante/registro.html", grupos=grupos,
                          error="Ese carnet ya está registrado.")
    iniciar_sesion(request, estudiante_id, carnet.strip(), grupo_id, f"{nombre.strip()} {apellido.strip()}")
    return redirect("/dashboard")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return redirect("/")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return redirect("/")

    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo = await periodo_activo(conn)
        if not periodo:
            return render(request, "estudiante/dashboard.html", nombre=request.session.get("estudiante_nombre"),
                          error="No hay ningún periodo de votación activo en este momento.")
        profesores = await conn.fetch(SQL_PROFESOR_DEL_GRUPO, request.session.get("grupo_id"))
        votados = [r["profesor_id"] for r in await conn.fetch(
            "SELECT profesor_id FROM voto WHERE estudiante_id = $1 AND periodo_id = $2",
            estudiante_id, periodo["id"])]

    return render(request, "estudiante/dashboard.html", nombre=request.session.get("estudiante_nombre"),
                  profesores=profesores, profesores_votados=votados, periodo=periodo)


@router.get("/votar/{profesor_id}", response_class=HTMLResponse)
async def formulario_votacion(request: Request, profesor_id: int):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return redirect("/")

    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo = await periodo_activo(conn)
        if not periodo:
            return redirect("/dashboard", request, "El periodo de votación está cerrado.")
        profesor = await conn.fetchrow(
            SQL_PROFESOR_DEL_GRUPO + " AND p.id = $2", request.session.get("grupo_id"), profesor_id)
        if not profesor:
            return redirect("/dashboard", request, "Ese profesor no está asignado a tu grupo.")
        if await ya_voto(conn, estudiante_id, profesor_id, periodo["id"]):
            return redirect("/dashboard", request, "Ya evaluaste a ese profesor en este periodo.")

    return render(request, "estudiante/votacion.html", profesor=profesor)


@router.post("/votar/{profesor_id}")
async def guardar_voto(request: Request, profesor_id: int):
    estudiante_id = request.session.get("estudiante_id")
    if not estudiante_id:
        return redirect("/")

    formulario = await request.form()
    try:
        notas = [int(formulario[f"aspecto_{i}"]) for i in range(1, 11)]
    except (KeyError, ValueError):
        return redirect(f"/votar/{profesor_id}", request, "Faltan respuestas: califica los 10 aspectos.")
    if not all(1 <= n <= 5 for n in notas):
        return redirect(f"/votar/{profesor_id}", request, "Las calificaciones deben ir del 1 al 5.")

    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo = await periodo_activo(conn)
        if not periodo:
            return redirect("/dashboard", request, "El periodo de votación está cerrado.")
        profesor = await conn.fetchrow(
            SQL_PROFESOR_DEL_GRUPO + " AND p.id = $2", request.session.get("grupo_id"), profesor_id)
        if not profesor:
            return redirect("/dashboard", request, "Ese profesor no está asignado a tu grupo.")
        try:
            await conn.execute(INSERT_VOTO, estudiante_id, profesor_id, periodo["id"], *notas)
        except UniqueViolationError:
            return redirect("/dashboard", request, "Ya habías evaluado a ese profesor.")

    return redirect("/dashboard", request, "¡Gracias! Tu evaluación anónima quedó registrada.")


def iniciar_sesion(request: Request, estudiante_id: int, carnet: str, grupo_id: int, nombre: str):
    request.session.update(estudiante_id=estudiante_id, estudiante_carnet=carnet,
                           grupo_id=grupo_id, estudiante_nombre=nombre)


async def ya_voto(conn, estudiante_id: int, profesor_id: int, periodo_id: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM voto WHERE estudiante_id = $1 AND profesor_id = $2 AND periodo_id = $3)",
        estudiante_id, profesor_id, periodo_id)
