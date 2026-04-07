import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "Name del proyecto de GCP")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

BUCKET_NAME = os.getenv("BUCKET_NAME", "nombre del bucket")

BQ_DATASET = os.getenv("BQ_DATASET", "dataset")
BQ_TABLE = os.getenv("BQ_TABLE", "scores_clientes")
BQ_VIEW = os.getenv("BQ_VIEW", "vw_scores_clientes")

MODEL_WARM_BLOB = "models/modelo_warm_start.pkl"
MODEL_COLD_BLOB = "models/modelo_cold_start.pkl"
KMEANS_BLOB = "models/kmeans_rfm.pkl"
SCALER_BLOB = "models/scaler_rfm.pkl"
MODEL_STATS_BLOB = "config/model_stats.json"

LOCAL_ARTIFACT_DIR = "/tmp/artifacts"