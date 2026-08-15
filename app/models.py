from pydantic import BaseModel, Field
from typing import Optional

# Esquema para el registro de estudiantes
class EstudianteRegistro(BaseModel):
    nombre: str
    apellido: str
    carnet: str
    grupo_id: int

# Esquema para la evaluación de profesores (10 preguntas)
# Usamos Field(..., ge=1, le=5) para validar que la nota sea del 1 al 5
class EvaluacionDocente(BaseModel):
    profesor_id: int
    aspecto_1: int = Field(..., ge=1, le=5, description="Dominio del tema")
    aspecto_2: int = Field(..., ge=1, le=5, description="Puntualidad")
    aspecto_3: int = Field(..., ge=1, le=5, description="Claridad en explicaciones")
    aspecto_4: int = Field(..., ge=1, le=5, description="Uso de recursos didácticos")
    aspecto_5: int = Field(..., ge=1, le=5, description="Resolución de dudas")
    aspecto_6: int = Field(..., ge=1, le=5, description="Evaluación justa")
    aspecto_7: int = Field(..., ge=1, le=5, description="Fomento de participación")
    aspecto_8: int = Field(..., ge=1, le=5, description="Trato respetuoso")
    aspecto_9: int = Field(..., ge=1, le=5, description="Organización de clases")
    aspecto_10: int = Field(..., ge=1, le=5, description="Cumplimiento del temario")

# Esquema para la creación/edición de un profesor (por parte del admin)
class ProfesorCreate(BaseModel):
    nombre: str
    apellido: str
    materias: str
    estado: bool = True
