# AGENTS.md

## What this is
FastAPI + Jinja2 teacher evaluation app. Deployed on Vercel. PostgreSQL via psycopg2.

## Run
    uvicorn main:app --reload

## Tests
    pytest

Requires live PostgreSQL. Set `DATABASE_URL` (or `POSTGRES_URL`) in `.env`.

## Gotchas

- **Auth is hardcoded** in `app/routes.py` (POST `/login`) and `static/js/index.js` (client-side). No env-based secrets — be careful not to expose or modify these carelessly.
- **No lint/format/typecheck** is configured for this repo.

## Rules

- **Pedir permiso antes de modificar archivos**: Cada vez que se modifique un archivo, se debe solicitar permiso al usuario antes de aplicar los cambios.
- **Testear al finalizar procesos**: Cada vez que termine algún proceso o tarea, se debe ejecutar un testeo para verificar que todo funciona correctamente.
