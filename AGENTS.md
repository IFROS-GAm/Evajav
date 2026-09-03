# AGENTS.md

## Qué es esto
App de evaluación docente anónima: FastAPI + Jinja2 + PostgreSQL (Supabase) con asyncpg.
Despliegue en Render (`render.yaml`).

## Ejecutar
    .\venv\Scripts\Activate.ps1
    uvicorn main:app --reload

    EVAJAV_TEST_OK=1 python tests/smoke.py   # 62 verificaciones, escribe en la base real

No hay linter ni typecheck configurados.

## Estructura
- `main.py` — app, sesiones, estáticos, handler de errores.
- `app/db.py` — pool de asyncpg (`get_pool`) y `periodo_activo()`.
- `app/web.py` — `render()` y `redirect()` (mensajes flash vía sesión).
- `app/routes_estudiante.py` — login por carnet, registro, dashboard, votación.
- `app/routes_admin.py` — login admin, periodos, reportes, gestión de administradores.
- `app/security.py` — hash y verificación de contraseñas (PBKDF2, solo stdlib).
- `templates/` + `static/css/app.css` — un solo CSS, sin estilos en línea.
- `database.md` — script SQL para crear el esquema en Supabase.

## Detalles que se pasan por alto
- **`statement_cache_size=0` es obligatorio** en `asyncpg.create_pool` (`app/db.py`): el pooler
  de Supabase (puerto 6543, pgbouncer en modo transaction) no soporta prepared statements y
  falla con `DuplicatePreparedStatementError`.
- **El pool es perezoso**: la app arranca aunque la base de datos esté caída o pausada.
- **Credenciales solo por entorno**: `DATABASE_URL`, `SECRET_KEY` y, para el primer
  arranque, `ADMIN_USERNAME` / `ADMIN_PASSWORD` en `.env` o en el panel de Render.
  `.env` nunca se commitea.
- **Los administradores viven en la tabla `administrador`** con contraseña hasheada. Las
  credenciales del `.env` solo sirven mientras esa tabla no tenga ninguna cuenta activa.
- **No pasar texto a un parámetro con cast** (`$1::timestamptz`): asyncpg infiere el tipo
  del cast y rechaza el `str`. Convertir en Python con `web.leer_fecha()`.
- **Fechas**: se guardan en UTC y se muestran con los filtros `|fecha` y `|dia` (zona de
  `ZONA_HORARIA`). No usar `.strftime()` directo en las plantillas.
- **`search_path` explícito en el pool**: detrás del pooler un `SET search_path` de otra
  aplicación se filtra entre conexiones.
- **Anonimato**: `voto` guarda `estudiante_id` únicamente para el constraint
  `UNIQUE(estudiante_id, profesor_id, periodo_id)`. Los reportes solo exponen promedios;
  no agregar consultas que relacionen estudiante con respuesta.
- **Un estudiante solo puede evaluar profesores de su grupo** (`profesor_grupo`): la
  validación está en `routes_estudiante.py`, no la quites.
- Profesores, grupos y asignaciones se administran desde el editor SQL de Supabase.

## Reglas
- Pedir permiso antes de modificar archivos.
- Probar al terminar cada tarea (mínimo: arrancar la app y recorrer las rutas).
