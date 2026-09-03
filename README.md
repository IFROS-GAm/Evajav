# Sistema de Evaluación Docente Anónima

Plataforma web (FastAPI + Jinja2) para que los estudiantes evalúen a sus profesores de forma
anónima. Base de datos PostgreSQL en Supabase y reportes con gráficos de radar (Chart.js).

## Características
- Ingreso de estudiantes por número de carnet y registro con selección de grupo.
- **Varios administradores** con contraseña hasheada (PBKDF2-SHA256) y dos roles:
  `superadmin` (gestiona usuarios) y `coordinador` (periodos y reportes).
- Cada estudiante solo ve y evalúa a los profesores asignados a su grupo.
- Un voto por profesor y por periodo, garantizado por la base de datos.
- Periodos de votación que el administrador abre y cierra.
- Reportes con promedios por profesor, visibles solo cuando el periodo está cerrado.
- Interfaz oscura, responsive y accesible con un único archivo CSS.

## Requisitos
- Python 3.12+
- Un proyecto en [Supabase](https://supabase.com/) (plan gratuito sirve).

## Instalación local

1. **Base de datos:** en el SQL Editor de Supabase ejecuta el contenido de `database.md`.
   Luego copia la cadena de conexión (Database → Connection string → URI, puerto 6543).

2. **Variables de entorno:** crea un archivo `.env` en la raíz:

   ```env
   DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=una-contraseña-propia
   SECRET_KEY=cadena-larga-y-aleatoria
   ```

3. **Dependencias:**

   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # Windows  (source venv/bin/activate en Mac/Linux)
   pip install -r requirements.txt
   ```

4. **Ejecutar:**

   ```bash
   uvicorn main:app --reload
   ```

   Disponible en `http://127.0.0.1:8000` (panel admin en `/admin`).

## Accesos
- **Estudiantes:** se registran en `/registro` con nombre, apellido, carnet y grupo.
- **Admin:** `/admin`. Mientras la tabla `administrador` esté vacía se entra con
  `ADMIN_USERNAME` / `ADMIN_PASSWORD` del `.env` **solo para crear el primer usuario**;
  en cuanto existe un administrador activo, esas credenciales dejan de funcionar.
- **Usuarios administradores:** `/admin/usuarios` (solo `superadmin`): crear cuentas,
  cambiar contraseñas y activar o desactivar. Siempre debe quedar uno activo.

## Pruebas

```bash
pip install -r requirements-dev.txt   # añade httpx, que solo usan las pruebas
EVAJAV_TEST_OK=1 python tests/smoke.py
```

62 verificaciones sobre las rutas reales. Escribe en la base de datos configurada en
`.env` y limpia lo que crea; por eso exige la variable de confirmación.

## Despliegue en Render
El repositorio incluye `render.yaml`. Al crear el servicio, Render usa:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Configura `DATABASE_URL`, `ADMIN_USERNAME` y `ADMIN_PASSWORD` en Environment
(`SECRET_KEY` la genera Render). Usa siempre la URL del **pooler** (puerto 6543).

## Notas técnicas
- `statement_cache_size=0` es obligatorio con el pooler de Supabase (pgbouncer en modo
  transaction); sin eso asyncpg falla con `DuplicatePreparedStatementError`.
- El `search_path` se fija en la conexión: el pooler comparte conexiones entre
  aplicaciones y un `SET` ajeno dejaría las consultas apuntando a otro esquema.
- Las fechas se guardan en UTC y se muestran en `ZONA_HORARIA` (por defecto
  `America/Bogota`), de ahí la dependencia `tzdata`.

## Administración de datos
Profesores, grupos y asignaciones profesor-grupo se gestionan desde el editor SQL de
Supabase (tablas `profesor`, `grupo`, `profesor_grupo`).
