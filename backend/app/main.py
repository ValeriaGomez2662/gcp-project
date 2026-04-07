from fastapi import FastAPI, HTTPException
from app.schemas import PredictRequest, ChatRequest, FilterClientsRequest
from app.models_loader import load_all_artifacts
from app.predictor import predict_score
from app.bq_tools import top_clients, filter_clients
from app.vertex_agent import agente_chat

app = FastAPI(title="Ferreycorp Propensión API")

artifacts = load_all_artifacts()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/top-clients")
def get_top_clients(limit: int = 10):
    try:
        return {"rows": top_clients(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict(payload: PredictRequest):
    try:
        result = predict_score(payload.model_dump(), artifacts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(payload: ChatRequest):
    try:
        return agente_chat(payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filter-clients")
def post_filter_clients(payload: FilterClientsRequest):
    try:
        rows = filter_clients(
            segmento=payload.segmento,
            prioridad=payload.prioridad,
            score_min=payload.score_min,
            dias_max=payload.dias_max,
            limit=payload.limit
        )
        return {"rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))