# Sistema de Evaluación Docente Anónima

Una plataforma web construida con FastAPI y Jinja2 que permite a los estudiantes evaluar a sus profesores de forma anónima, utilizando Supabase (PostgreSQL) como base de datos y Chart.js para la visualización de resultados.

## Características
- Diseño Neumórfico Oscuro (Neumorphism).
- Validaciones de votos únicos mediante Carnet de Estudiante.
- Asignación de profesores por grupo.
- Panel administrativo con generación de reportes (solo visibles al cerrar el periodo).

## Requisitos Previos
- Python 3.12+
- Una cuenta en [Supabase](https://supabase.com/) (gratuita).

## Instalación y Ejecución Local

1. **Configurar la Base de Datos:**
   - Ve a Supabase, crea un nuevo proyecto.
   - En el SQL Editor de Supabase, pega y ejecuta el contenido del archivo `database.md`.
   - Ve a los ajustes de base de datos (Database -> Connection string -> URI) y copia la URL de conexión.

2. **Configurar Entorno:**
   - Renombra el archivo `.env.example` a `.env` (o crea uno nuevo).
   - Remplaza la variable `DATABASE_URL` por la URL de tu base de datos Supabase.

3. **Instalar Dependencias:**
   Se recomienda usar un entorno virtual:
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\Activate.ps1
   # En Mac/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

4. **Ejecutar la Aplicación:**
   ```bash
   uvicorn main:app --reload
   ```
   La aplicación estará disponible en `http://127.0.0.1:8000`.

## Accesos por Defecto
- **Estudiantes**: Necesitan registrarse previamente para poder iniciar sesión. Pueden usar un carnet inventado para pruebas.
- **Admin**: Accede en la ruta `/admin` usando el usuario y contraseña definidos en el archivo `.env` (por defecto `admin` / `admin123`).
