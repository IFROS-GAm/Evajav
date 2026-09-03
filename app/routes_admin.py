import os
from secrets import compare_digest

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.db import get_pool, periodo_activo
from app.security import hash_password, password_debil, verify_password
from app.web import leer_fecha, redirect, render

router = APIRouter(prefix="/admin")

# Credenciales de arranque: solo sirven mientras no exista ningún administrador en la
# base de datos. En cuanto se crea el primero, dejan de funcionar.
ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

SQL_PROMEDIOS = """
    SELECT p.nombre, p.apellido, COUNT(v.id) AS cantidad_votos,
           ROUND(AVG(v.aspecto_1_dominio_tema), 1) AS a1,
           ROUND(AVG(v.aspecto_2_puntualidad), 1) AS a2,
           ROUND(AVG(v.aspecto_3_claridad_explicacion), 1) AS a3,
           ROUND(AVG(v.aspecto_4_recursos_didacticos), 1) AS a4,
           ROUND(AVG(v.aspecto_5_resolucion_dudas), 1) AS a5,
           ROUND(AVG(v.aspecto_6_evaluacion_justa), 1) AS a6,
           ROUND(AVG(v.aspecto_7_fomento_participacion), 1) AS a7,
           ROUND(AVG(v.aspecto_8_trato_respetuoso), 1) AS a8,
           ROUND(AVG(v.aspecto_9_organizacion_clase), 1) AS a9,
           ROUND(AVG(v.aspecto_10_cumplimiento_temario), 1) AS a10
    FROM voto v JOIN profesor p ON p.id = v.profesor_id
    WHERE v.periodo_id = $1
    GROUP BY p.id, p.nombre, p.apellido
    ORDER BY p.apellido
"""


def es_admin(request: Request) -> bool:
    return request.session.get("is_admin") is True


def es_superadmin(request: Request) -> bool:
    return es_admin(request) and request.session.get("admin_rol") == "superadmin"


async def hay_administradores(conn) -> bool:
    return await conn.fetchval("SELECT EXISTS (SELECT 1 FROM administrador WHERE activo = true)")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_inicio(request: Request):
    return redirect("/admin/dashboard" if es_admin(request) else "/admin/login")


@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    if es_admin(request):
        return redirect("/admin/dashboard")
    return render(request, "admin/login.html")


@router.post("/login")
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        cuenta = await conn.fetchrow(
            "SELECT id, usuario, nombre, password_hash, rol FROM administrador "
            "WHERE lower(usuario) = lower($1) AND activo = true", username.strip())
        if cuenta and verify_password(password, cuenta["password_hash"]):
            request.session.update(is_admin=True, admin_id=cuenta["id"], admin_rol=cuenta["rol"],
                                   admin_nombre=cuenta["nombre"])
            await conn.execute("UPDATE administrador SET ultimo_acceso = now() WHERE id = $1", cuenta["id"])
            return redirect("/admin/dashboard")
        # Arranque inicial: sin administradores en la base, valen las credenciales del entorno.
        if not await hay_administradores(conn) and compare_digest(username.encode(), ADMIN_USER.encode()) \
                and compare_digest(password.encode(), ADMIN_PASS.encode()):
            request.session.update(is_admin=True, admin_id=None, admin_rol="superadmin",
                                   admin_nombre="Acceso inicial")
            return redirect("/admin/usuarios", request,
                            "Acceso inicial: crea tu usuario administrador. Al hacerlo, estas credenciales dejan de servir.")

    return render(request, "admin/login.html", error="Credenciales incorrectas.")


@router.get("/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return redirect("/admin/login")


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not es_admin(request):
        return redirect("/admin/login")

    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo = await periodo_activo(conn)
        stats = await conn.fetchrow(
            "SELECT (SELECT count(*) FROM voto) AS votos, "
            "(SELECT count(*) FROM estudiante) AS estudiantes, "
            "(SELECT count(*) FROM profesor WHERE estado = true) AS profesores")
        sin_admins = not await hay_administradores(conn)

    return render(request, "admin/dashboard.html", periodo_activo=periodo, stats=stats, sin_admins=sin_admins)


@router.post("/periodo/nuevo")
async def admin_nuevo_periodo(request: Request, fecha_fin: str = Form(...)):
    if not es_admin(request):
        return redirect("/admin/login")

    try:
        limite = leer_fecha(fecha_fin)
    except ValueError:
        return redirect("/admin/dashboard", request, "La fecha de cierre no es válida.")

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE periodo_votacion SET estado = false WHERE estado = true")
            await conn.execute("INSERT INTO periodo_votacion (fecha_fin) VALUES ($1)", limite)
    return redirect("/admin/dashboard", request, "Periodo abierto correctamente.")


@router.post("/periodo/cerrar")
async def admin_cerrar_periodo(request: Request):
    if not es_admin(request):
        return redirect("/admin/login")

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE periodo_votacion SET estado = false WHERE estado = true")
    return redirect("/admin/dashboard", request, "Periodo cerrado. Ya puedes ver los reportes.")


@router.get("/reportes", response_class=HTMLResponse)
async def admin_reportes(request: Request):
    if not es_admin(request):
        return redirect("/admin/login")

    pool = await get_pool()
    async with pool.acquire() as conn:
        periodo = await conn.fetchrow(
            "SELECT id, fecha_inicio, fecha_fin FROM periodo_votacion "
            "WHERE estado = false OR fecha_fin < NOW() ORDER BY fecha_fin DESC LIMIT 1")
        if not periodo:
            return render(request, "admin/reportes.html",
                          error="Todavía no hay periodos cerrados. Cierra el periodo actual para ver resultados.")
        resultados = await conn.fetch(SQL_PROMEDIOS, periodo["id"])

    return render(request, "admin/reportes.html", periodo=periodo, resultados=resultados)


# ---------------------------------------------------------------- administradores

@router.get("/usuarios", response_class=HTMLResponse)
async def admin_usuarios(request: Request):
    if not es_superadmin(request):
        return redirect("/admin/dashboard", request, "Solo un superadministrador gestiona usuarios.")

    pool = await get_pool()
    async with pool.acquire() as conn:
        usuarios = await conn.fetch(
            "SELECT id, usuario, nombre, rol, activo, ultimo_acceso, created_at "
            "FROM administrador ORDER BY activo DESC, usuario")
    return render(request, "admin/usuarios.html", usuarios=usuarios, yo=request.session.get("admin_id"))


@router.post("/usuarios/nuevo")
async def admin_usuario_nuevo(request: Request, usuario: str = Form(...), nombre: str = Form(...),
                              password: str = Form(...), rol: str = Form("coordinador")):
    if not es_superadmin(request):
        return redirect("/admin/dashboard")
    if rol not in ("superadmin", "coordinador"):
        return redirect("/admin/usuarios", request, "Rol no válido.")
    problema = password_debil(password)
    if problema:
        return redirect("/admin/usuarios", request, problema)

    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO administrador (usuario, nombre, password_hash, rol) VALUES ($1, $2, $3, $4)",
                usuario.strip().lower(), nombre.strip(), hash_password(password), rol)
        except UniqueViolationError:
            return redirect("/admin/usuarios", request, f"El usuario «{usuario}» ya existe.")
    return redirect("/admin/usuarios", request, f"Administrador «{usuario}» creado.")


@router.post("/usuarios/{usuario_id}/password")
async def admin_usuario_password(request: Request, usuario_id: int, password: str = Form(...)):
    if not es_superadmin(request):
        return redirect("/admin/dashboard")
    problema = password_debil(password)
    if problema:
        return redirect("/admin/usuarios", request, problema)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE administrador SET password_hash = $1 WHERE id = $2",
                           hash_password(password), usuario_id)
    return redirect("/admin/usuarios", request, "Contraseña actualizada.")


@router.post("/usuarios/{usuario_id}/estado")
async def admin_usuario_estado(request: Request, usuario_id: int):
    if not es_superadmin(request):
        return redirect("/admin/dashboard")
    if usuario_id == request.session.get("admin_id"):
        return redirect("/admin/usuarios", request, "No puedes desactivar tu propia cuenta.")

    pool = await get_pool()
    async with pool.acquire() as conn:
        activo = await conn.fetchval(
            "UPDATE administrador SET activo = NOT activo WHERE id = $1 RETURNING activo", usuario_id)
        if activo is False and not await hay_administradores(conn):
            await conn.execute("UPDATE administrador SET activo = true WHERE id = $1", usuario_id)
            return redirect("/admin/usuarios", request, "Debe quedar al menos un administrador activo.")
    return redirect("/admin/usuarios", request, "Cuenta activada." if activo else "Cuenta desactivada.")
