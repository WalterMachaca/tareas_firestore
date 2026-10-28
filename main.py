import os
from datetime import datetime, timezone
from typing import Optional
from weakref import ref
from annotated_types import doc
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# --- Conexión con Firestore ---
RUTA_LLAVE = os.getenv("FIREBASE_KEY", "serviceAccountKey.json")
credenciales = credentials.Certificate(RUTA_LLAVE)
firebase_admin.initialize_app(credenciales)
db = firestore.client()
tareas = db.collection("tareas")

# --- Esquemas ---
class TareaCrear(BaseModel):
    
    titulo: str = Field(min_length=3, max_length=100)
    descripcion: Optional[str] = None
    prioridad: int = Field(default=1, ge=1, le=3)

class TareaActualizar(BaseModel):

    titulo: Optional[str] = Field(default=None, min_length=3, max_length=100)
    descripcion: Optional[str] = None
    prioridad: Optional[int] = Field(default=None, ge=1, le=3)
    completada: Optional[bool] = None

class TareaRespuesta(BaseModel):
    
    id: str
    titulo: str
    descripcion: Optional[str] = None
    prioridad: int
    completada: bool
    creada: datetime

def a_respuesta(doc) -> TareaRespuesta:
    return TareaRespuesta(id=doc.id, **doc.to_dict())
app = FastAPI(title="API de Tareas con Firestore")

@app.post("/tareas", response_model=TareaRespuesta,
status_code=status.HTTP_201_CREATED)
def crear_tarea(datos: TareaCrear):
    nueva = datos.model_dump()
    nueva["completada"] = False
    nueva["creada"] = datetime.now(timezone.utc)
    _, ref = tareas.add(nueva) # Firestore genera el ID
    return a_respuesta(ref.get())

@app.get("/tareas", response_model=list[TareaRespuesta])
def listar_tareas(completada: Optional[bool] = None):
    consulta = tareas
    if completada is not None:
        consulta = tareas.where(filter=FieldFilter("completada", "==", completada))
    return [a_respuesta(d) for d in consulta.stream()]

@app.get("/tareas/{tarea_id}", response_model=TareaRespuesta)
def obtener_tarea(tarea_id: str):
    doc = tareas.document(tarea_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return a_respuesta(doc)

@app.patch("/tareas/{tarea_id}", response_model=TareaRespuesta)
def actualizar_tarea(tarea_id: str, datos: TareaActualizar):
    ref = tareas.document(tarea_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=400, detail="No se envió ningún campo")
    ref.update(cambios)
    return a_respuesta(ref.get())

@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(tarea_id: str):
    ref = tareas.document(tarea_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    ref.delete()