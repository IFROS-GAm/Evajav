-- ==============================================================================
-- SISTEMA DE EVALUACIÓN DOCENTE ANÓNIMA - SCRIPT PARA SUPABASE
-- Pega este contenido en el SQL Editor de Supabase y presiona "Run"
-- ==============================================================================

-- 1. Crear tabla de Periodos de Votación
-- Controla cuándo los estudiantes pueden o no emitir votos.
CREATE TABLE periodo_votacion (
    id SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP WITH TIME ZONE NOT NULL,
    estado BOOLEAN DEFAULT true, -- true = activo, false = inactivo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Crear tabla de Grupos
-- Los grupos o grados (ej. 8-4, 9-4) a los que pertenecen los estudiantes.
CREATE TABLE grupo (
    id SERIAL PRIMARY KEY,
    codigo_grupo TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Crear tabla de Estudiantes
-- Guarda el registro de los estudiantes. El carnet es único para evitar duplicados.
CREATE TABLE estudiante (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    carnet TEXT UNIQUE NOT NULL, -- Llave única para la autenticación y control
    grupo_id INTEGER REFERENCES grupo(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Crear tabla de Profesores
CREATE TABLE profesor (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    materias TEXT NOT NULL,
    estado BOOLEAN DEFAULT true, -- true = activo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Crear tabla de Asignación Profesor - Grupo
-- Define qué grupos tienen permitido votar por qué profesor.
CREATE TABLE profesor_grupo (
    profesor_id INTEGER REFERENCES profesor(id) ON DELETE CASCADE,
    grupo_id INTEGER REFERENCES grupo(id) ON DELETE CASCADE,
    PRIMARY KEY (profesor_id, grupo_id)
);

-- 6. Crear tabla de Votos
-- IMPORTANTE: Aunque se guarda el estudiante_id para evitar que vote dos veces
-- por el mismo profesor en el mismo periodo, el frontend/backend JAMÁS expondrá 
-- esta relación. Siempre se visualizará de forma agregada (promedios).
CREATE TABLE voto (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiante(id) ON DELETE RESTRICT,
    profesor_id INTEGER REFERENCES profesor(id) ON DELETE RESTRICT,
    periodo_id INTEGER REFERENCES periodo_votacion(id) ON DELETE RESTRICT,
    
    -- Los 10 aspectos a evaluar (notas del 1 al 5)
    aspecto_1_dominio_tema INTEGER CHECK (aspecto_1_dominio_tema BETWEEN 1 AND 5),
    aspecto_2_puntualidad INTEGER CHECK (aspecto_2_puntualidad BETWEEN 1 AND 5),
    aspecto_3_claridad_explicacion INTEGER CHECK (aspecto_3_claridad_explicacion BETWEEN 1 AND 5),
    aspecto_4_recursos_didacticos INTEGER CHECK (aspecto_4_recursos_didacticos BETWEEN 1 AND 5),
    aspecto_5_resolucion_dudas INTEGER CHECK (aspecto_5_resolucion_dudas BETWEEN 1 AND 5),
    aspecto_6_evaluacion_justa INTEGER CHECK (aspecto_6_evaluacion_justa BETWEEN 1 AND 5),
    aspecto_7_fomento_participacion INTEGER CHECK (aspecto_7_fomento_participacion BETWEEN 1 AND 5),
    aspecto_8_trato_respetuoso INTEGER CHECK (aspecto_8_trato_respetuoso BETWEEN 1 AND 5),
    aspecto_9_organizacion_clase INTEGER CHECK (aspecto_9_organizacion_clase BETWEEN 1 AND 5),
    aspecto_10_cumplimiento_temario INTEGER CHECK (aspecto_10_cumplimiento_temario BETWEEN 1 AND 5),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint crucial: Un estudiante solo puede votar 1 vez por profesor en un periodo dado
    CONSTRAINT unico_voto_estudiante_profesor UNIQUE(estudiante_id, profesor_id, periodo_id)
);

-- ==============================================================================
-- DATOS DE PRUEBA (Opcional, para facilitar el desarrollo inicial)
-- ==============================================================================

-- Insertar un periodo de prueba activo (vence en 30 días)
INSERT INTO periodo_votacion (fecha_fin) VALUES (NOW() + INTERVAL '30 days');

-- Insertar grupos de prueba
INSERT INTO grupo (codigo_grupo) VALUES ('8-4'), ('9-4'), ('10-1');

-- Insertar profesores de prueba
INSERT INTO profesor (nombre, apellido, materias) VALUES 
('Sebastián', 'Agudelo', 'Matemáticas, Física'),
('Laura', 'Martínez', 'Programación, Base de Datos');

-- Asignar profesores a grupos (Sebastián a 8-4 y 9-4. Laura a 9-4 y 10-1)
INSERT INTO profesor_grupo (profesor_id, grupo_id) VALUES 
(1, 1), (1, 2), -- Sebastián (Matemáticas) da clase a 8-4 y 9-4
(2, 2), (2, 3); -- Laura (Programación) da clase a 9-4 y 10-1

-- Insertar un estudiante de prueba (Estudiante en 9-4)
-- IMPORTANTE: Cambia el ID de grupo según corresponda. El grupo 2 es '9-4'.
INSERT INTO estudiante (nombre, apellido, carnet, grupo_id) VALUES 
('Juan', 'Pérez', '20231001', 2);

-- ==============================================================================
-- MIGRACIÓN 2026-09: administradores múltiples con contraseña hasheada
-- Ejecuta este bloque en el SQL Editor de Supabase si ya tenías la base creada.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS administrador (
    id SERIAL PRIMARY KEY,
    usuario TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    password_hash TEXT NOT NULL,          -- pbkdf2_sha256$iteraciones$salt$hash
    rol TEXT NOT NULL DEFAULT 'coordinador' CHECK (rol IN ('superadmin', 'coordinador')),
    activo BOOLEAN NOT NULL DEFAULT true,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Mientras esta tabla no tenga ninguna cuenta activa, el login de /admin acepta
-- ADMIN_USERNAME / ADMIN_PASSWORD del .env solo para crear el primer usuario.
