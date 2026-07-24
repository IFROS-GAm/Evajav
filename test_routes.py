import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_oPTpmYIz47hH@ep-withered-rain-atkd67fc-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

with patch("app.db.init_db", new_callable=AsyncMock):
    from main import app

client = TestClient(app)


def test_index_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "EVAJ" in r.text


def test_login_admin_ok():
    r = client.post("/login", data={"username": "999", "password": "ADMIN_MJAVIERA"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/administrador"


def test_login_student_ok():
    r = client.post("/login", data={"username": "10", "password": "M"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/seleccionatuprofesor"


def test_login_bad_credentials():
    r = client.post("/login", data={"username": "wrong", "password": "wrong"})
    assert r.status_code == 401


def test_admin_page():
    r = client.get("/administrador")
    assert r.status_code == 200
    assert "Perfil Administrador" in r.text


def test_gestion_profesores():
    r = client.get("/gestionProfesores")
    assert r.status_code == 200
    assert "Elige un profesor" in r.text


def test_gestion_profesores_informacion():
    r = client.get("/gestionProfesoresInformacion")
    assert r.status_code == 200
    assert "Información del Profesor" in r.text


def test_select_profesor():
    r = client.get("/seleccionatuprofesor")
    assert r.status_code == 200
    assert "¿A quién vas a evaluar?" in r.text


def test_configuracion():
    r = client.get("/configuracion")
    assert r.status_code == 200


def test_califica_profesor():
    r = client.get("/calificaElProfesor")
    assert r.status_code == 200


def test_agradecimiento():
    r = client.get("/Agradecimiento")
    assert r.status_code == 200
