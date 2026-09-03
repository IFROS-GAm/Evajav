"""
Prueba de humo de evaJav: recorre las rutas reales de estudiante y administrador.

OJO: corre contra la base de datos configurada en .env, que es la de producción.
Crea un estudiante de prueba, un par de administradores y un periodo, y lo borra
todo al terminar. Para evitar accidentes exige una confirmación explícita:

    $env:EVAJAV_TEST_OK = "1"; python tests/smoke.py     # PowerShell
    EVAJAV_TEST_OK=1 python tests/smoke.py               # bash
"""
import os
import sys

if os.getenv("EVAJAV_TEST_OK") != "1":
    sys.exit("Cancelado: define EVAJAV_TEST_OK=1 para permitir que las pruebas escriban en la base real.")

import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
import main
from app.db import get_pool, close_db

CARNET = "TEST-CLAUDE-999"
ok = fail = 0

def check(nombre, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1; print("PASS", nombre)
    else:
        fail += 1; print("FAIL", nombre, extra)

async def limpiar():
    pool = await get_pool()
    async with pool.acquire() as c:
        est = await c.fetchval("SELECT id FROM estudiante WHERE carnet = $1", CARNET)
        if est:
            await c.execute("DELETE FROM voto WHERE estudiante_id = $1", est)
            await c.execute("DELETE FROM estudiante WHERE id = $1", est)
        await c.execute("DELETE FROM periodo_votacion WHERE fecha_fin > '2029-01-01'")
        await c.execute("UPDATE periodo_votacion SET estado = true WHERE id = (SELECT max(id) FROM periodo_votacion)")
    await close_db()

with TestClient(main.app) as c:
    r = c.get("/"); check("GET / 200", r.status_code == 200 and "carnet" in r.text.lower(), r.status_code)
    r = c.get("/registro"); check("GET /registro tiene grupos", r.status_code == 200 and "9-4" in r.text)
    r = c.post("/registro", data={"nombre": "Test", "apellido": "Claude", "carnet": CARNET, "grupo_id": 2},
               follow_redirects=False)
    check("POST /registro -> /dashboard", r.status_code == 303 and r.headers["location"] == "/dashboard", r.status_code)
    r = c.post("/registro", data={"nombre": "Test", "apellido": "Claude", "carnet": CARNET, "grupo_id": 2})
    check("registro duplicado avisa", "ya está registrado" in r.text)

    r = c.get("/dashboard")
    check("dashboard lista profes del grupo", r.status_code == 200 and "Sebasti" in r.text and "Laura" in r.text)
    check("dashboard NO filtra otros grupos", r.text.count("/votar/") == 2, r.text.count("/votar/"))

    r = c.get("/votar/1"); check("GET /votar/1 (mi grupo) 200", r.status_code == 200 and "Dominio del tema" in r.text)
    r = c.get("/votar/999", follow_redirects=False)
    check("profesor inexistente -> redirect", r.status_code == 303 and r.headers["location"] == "/dashboard")

    notas = {f"aspecto_{i}": str((i % 5) + 1) for i in range(1, 11)}
    r = c.post("/votar/1", data=notas, follow_redirects=False)
    check("POST voto valido -> /dashboard", r.status_code == 303 and r.headers["location"] == "/dashboard", r.status_code)
    r = c.get("/dashboard"); check("flash de gracias", "Gracias" in r.text)
    r = c.get("/dashboard"); check("flash se consume una vez", "Gracias" not in r.text)
    check("marca ya evaluado", "Ya evaluado" in r.text)

    r = c.get("/votar/1", follow_redirects=False)
    check("no deja re-votar", r.status_code == 303)
    r = c.get("/dashboard"); check("aviso ya evaluado", "Ya evaluaste" in r.text)

    r = c.post("/votar/1", data=notas, follow_redirects=False); c.get("/dashboard")
    check("POST duplicado no rompe", r.status_code == 303)
    r = c.post("/votar/2", data={f"aspecto_{i}": "9" for i in range(1, 11)}, follow_redirects=False)
    check("nota fuera de rango rechazada", r.status_code == 303 and "/votar/2" in r.headers["location"])
    r = c.post("/votar/2", data={"aspecto_1": "3"}, follow_redirects=False)
    check("faltan respuestas rechazado", r.status_code == 303 and "/votar/2" in r.headers["location"])

    r = c.get("/votar/3", follow_redirects=False)
    check("profe de otro grupo bloqueado", r.status_code == 303 and r.headers["location"] == "/dashboard")

    c.get("/logout")
    r = c.get("/dashboard", follow_redirects=False); check("sin sesion -> /", r.headers.get("location") == "/")

# --- Admin ---
with TestClient(main.app) as c:
    r = c.get("/admin", follow_redirects=False)
    check("/admin redirige a login", r.status_code == 303 and r.headers["location"] == "/admin/login")
    r = c.post("/admin/login", data={"username": "admin", "password": "malaclave"})
    check("login admin malo avisa", "incorrectas" in r.text)
    r = c.post("/admin/login", data={"username": os.getenv("ADMIN_USERNAME", "admin"),
                                     "password": os.getenv("ADMIN_PASSWORD", "admin123")}, follow_redirects=False)
    check("login admin ok", r.status_code == 303 and r.headers["location"] in ("/admin/dashboard", "/admin/usuarios"), r.status_code)
    r = c.get("/admin/dashboard")
    check("dashboard admin 200", r.status_code == 200 and "Panel de control" in r.text)
    check("dashboard muestra periodo abierto", "Abierto" in r.text)
    r = c.get("/admin/reportes")
    check("reportes sin periodo cerrado avisa", "no hay periodos cerrados" in r.text.lower(), r.text[:200])

    r = c.post("/admin/periodo/cerrar", follow_redirects=False); check("cerrar periodo 303", r.status_code == 303)
    r = c.get("/admin/reportes")
    check("reportes con datos", r.status_code == 200 and "canvas" in r.text and "chart.js" in r.text.lower())
    # Los periodos nuevos se prueban al final: cambian cuál es "el ultimo periodo cerrado".
    r = c.post("/admin/periodo/nuevo", data={"fecha_fin": "2030-12-31T23:59"}, follow_redirects=False)
    check("abrir periodo nuevo", r.status_code == 303)
    r = c.get("/admin/dashboard")
    check("periodo nuevo queda activo", "Activo hasta" in r.text or "31/12/2030" in r.text, r.text.count("31/12/2030"))
    r = c.post("/admin/periodo/nuevo", data={"fecha_fin": "no-es-fecha"}, follow_redirects=False)
    c.get("/admin/dashboard"); check("fecha invalida no rompe", r.status_code == 303)
    r = c.get("/dashboard", follow_redirects=False); check("admin no entra a dashboard alumno", r.headers.get("location") == "/")

with TestClient(main.app) as c:
    r = c.get("/admin/dashboard", follow_redirects=False)
    check("sin sesion admin -> login", r.headers.get("location") == "/admin/login")
    r = c.get("/favicon.ico"); check("favicon 200", r.status_code == 200)

asyncio.run(limpiar())


# ============================ Administradores múltiples ============================

PWD = "Claude12345"
async def limpiar_admins():
    pool = await get_pool()
    async with pool.acquire() as c:
        await c.execute("DELETE FROM administrador WHERE usuario LIKE 'test.%'")
    await close_db()

env_user = os.getenv("ADMIN_USERNAME", "admin")
env_pass = os.getenv("ADMIN_PASSWORD", "admin123")

# 1. Sin administradores en la base: el acceso inicial del .env funciona
with TestClient(main.app) as c:
    r = c.post("/admin/login", data={"username": env_user, "password": env_pass}, follow_redirects=False)
    check("bootstrap .env entra", r.status_code == 303 and r.headers["location"] == "/admin/usuarios", r.status_code)
    r = c.get("/admin/usuarios")
    check("aviso de crear primer admin", "crea tu usuario administrador" in r.text.lower())
    check("tabla vacia", "Sin administradores todavía" in r.text)
    r = c.get("/admin/dashboard")
    check("dashboard avisa sin admins", "No hay administradores en la base" in r.text)

    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.super", "nombre": "Test Super",
                                              "password": "123", "rol": "superadmin"}, follow_redirects=False)
    c.get("/admin/usuarios")
    check("password debil rechazada", r.status_code == 303)
    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.super", "nombre": "Test Super",
                                              "password": PWD, "rol": "superadmin"}, follow_redirects=False)
    check("crea superadmin", r.status_code == 303)
    r = c.get("/admin/usuarios")
    check("aparece en la tabla", "test.super" in r.text and "superadmin" in r.text)
    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.super", "nombre": "Otro",
                                              "password": PWD, "rol": "coordinador"}, follow_redirects=False)
    check("usuario duplicado rechazado", r.status_code == 303)
    r = c.get("/admin/usuarios"); check("avisa duplicado", "ya existe" in r.text)
    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.coord", "nombre": "Test Coord",
                                              "password": PWD, "rol": "coordinador"}, follow_redirects=False)
    check("crea coordinador", r.status_code == 303)
    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.hack", "nombre": "Hack",
                                              "password": PWD, "rol": "root"}, follow_redirects=False)
    c.get("/admin/usuarios"); check("rol invalido rechazado", r.status_code == 303)

# 2. Ya hay administradores: el acceso del .env queda cerrado
with TestClient(main.app) as c:
    r = c.post("/admin/login", data={"username": env_user, "password": env_pass})
    check("bootstrap .env ya NO entra", "incorrectas" in r.text)
    r = c.post("/admin/login", data={"username": "test.super", "password": "malo"})
    check("password erronea rechazada", "incorrectas" in r.text)
    r = c.post("/admin/login", data={"username": "TEST.SUPER", "password": PWD}, follow_redirects=False)
    check("login superadmin (case-insensitive)", r.status_code == 303 and r.headers["location"] == "/admin/dashboard")
    r = c.get("/admin/dashboard")
    check("nav muestra Usuarios a superadmin", "/admin/usuarios" in r.text and "Test Super" in r.text)
    check("ya no avisa sin admins", "No hay administradores en la base" not in r.text)
    r = c.get("/admin/usuarios")
    check("ultimo acceso registrado", "test.super" in r.text)
    yo = [l for l in r.text.splitlines() if "test.super" in l]
    check("se marca la cuenta propia", any("tú" in l for l in yo))

# 3. Coordinador: entra pero no gestiona usuarios
with TestClient(main.app) as c:
    r = c.post("/admin/login", data={"username": "test.coord", "password": PWD}, follow_redirects=False)
    check("login coordinador", r.status_code == 303)
    r = c.get("/admin/dashboard")
    check("coordinador NO ve link Usuarios", "/admin/usuarios" not in r.text)
    r = c.get("/admin/usuarios", follow_redirects=False)
    check("coordinador bloqueado en /usuarios", r.status_code == 303 and r.headers["location"] == "/admin/dashboard")
    r = c.get("/admin/dashboard"); check("avisa falta de permiso", "superadministrador" in r.text)
    r = c.post("/admin/usuarios/nuevo", data={"usuario": "test.x", "nombre": "X", "password": PWD},
               follow_redirects=False)
    check("coordinador no crea admins", r.status_code == 303 and r.headers["location"] == "/admin/dashboard")

# 4. Reglas de seguridad sobre las cuentas
async def ids():
    pool = await get_pool()
    async with pool.acquire() as conn:
        f = {r["usuario"]: r["id"] for r in await conn.fetch("SELECT usuario, id FROM administrador WHERE usuario LIKE 'test.%'")}
    await close_db()
    return f
mapa = asyncio.run(ids())

with TestClient(main.app) as c:
    c.post("/admin/login", data={"username": "test.super", "password": PWD})
    r = c.post(f"/admin/usuarios/{mapa['test.super']}/estado", follow_redirects=False)
    c.get("/admin/usuarios")
    check("no puede desactivarse a si mismo", r.status_code == 303)
    r = c.post(f"/admin/usuarios/{mapa['test.coord']}/estado", follow_redirects=False)
    check("desactiva a otro", r.status_code == 303)
    r = c.get("/admin/usuarios"); check("queda inactivo", "inactivo" in r.text)
    r = c.post(f"/admin/usuarios/{mapa['test.coord']}/password", data={"password": "nuevaClave99"},
               follow_redirects=False)
    check("cambia password de otro", r.status_code == 303)

with TestClient(main.app) as c:
    r = c.post("/admin/login", data={"username": "test.coord", "password": "nuevaClave99"})
    check("cuenta inactiva no entra", "incorrectas" in r.text)

with TestClient(main.app) as c:
    r = c.get("/admin/usuarios", follow_redirects=False)
    check("sin sesion no ve usuarios", r.headers.get("location") == "/admin/dashboard")

asyncio.run(limpiar())
asyncio.run(limpiar_admins())
print(f"\n== {ok} PASS / {fail} FAIL ==")
sys.exit(1 if fail else 0)
