from pydantic import BaseModel
from typing import Optional, Dict, Any

class PredictRequest(BaseModel):
    edad: int
    genero: int
    estado_civil: int
    nivel_educacion: int
    ingreso_anual: float
    ocupacion: int

    precio_marca_1: float
    precio_marca_2: float
    precio_marca_3: float
    precio_marca_4: float
    precio_marca_5: float

    promo_marca_1: int
    promo_marca_2: int
    promo_marca_3: int
    promo_marca_4: int
    promo_marca_5: int

    ultima_marca_comprada: Optional[int] = None
    ultima_cantidad_comprada: Optional[int] = None
    dias_desde_ultima_compra: Optional[float] = None
    compras_acumuladas: Optional[float] = None
    tasa_compra_historica: Optional[float] = None
    frecuencia_compras_30d: Optional[float] = None
    compras_ultimas_3_visitas: Optional[float] = None
    habia_comprado_ayer: Optional[int] = None
    dia_visita: Optional[int] = 730

class ChatRequest(BaseModel):
    message: str

class FilterClientsRequest(BaseModel):
    segmento: Optional[str] = None
    prioridad: Optional[str] = None
    score_min: Optional[float] = None
    dias_max: Optional[float] = None
    limit: int = 10