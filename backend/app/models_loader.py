import os
import json
import joblib
from google.cloud import storage
from .config import PROJECT_ID

from .config import (
    BUCKET_NAME,
    MODEL_WARM_BLOB,
    MODEL_COLD_BLOB,
    KMEANS_BLOB,
    SCALER_BLOB,
    MODEL_STATS_BLOB,
    LOCAL_ARTIFACT_DIR
)

os.makedirs(LOCAL_ARTIFACT_DIR, exist_ok=True)

storage_client = storage.Client(project=PROJECT_ID)

def download_blob(bucket_name: str, blob_name: str, local_path: str):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)

def ensure_artifacts():
    files = {
        MODEL_WARM_BLOB: f"{LOCAL_ARTIFACT_DIR}/modelo_warm_start.pkl",
        MODEL_COLD_BLOB: f"{LOCAL_ARTIFACT_DIR}/modelo_cold_start.pkl",
        KMEANS_BLOB: f"{LOCAL_ARTIFACT_DIR}/kmeans_rfm.pkl",
        SCALER_BLOB: f"{LOCAL_ARTIFACT_DIR}/scaler_rfm.pkl",
        MODEL_STATS_BLOB: f"{LOCAL_ARTIFACT_DIR}/model_stats.json",
    }

    for blob_name, local_path in files.items():
        if not os.path.exists(local_path):
            download_blob(BUCKET_NAME, blob_name, local_path)

    return files

def load_all_artifacts():
    files = ensure_artifacts()

    model_warm = joblib.load(files[MODEL_WARM_BLOB])
    model_cold = joblib.load(files[MODEL_COLD_BLOB])
    kmeans_rfm = joblib.load(files[KMEANS_BLOB])
    scaler_rfm = joblib.load(files[SCALER_BLOB])

    with open(files[MODEL_STATS_BLOB], "r", encoding="utf-8") as f:
        model_stats = json.load(f)

    return {
        "model_warm": model_warm,
        "model_cold": model_cold,
        "kmeans_rfm": kmeans_rfm,
        "scaler_rfm": scaler_rfm,
        "model_stats": model_stats,
    }