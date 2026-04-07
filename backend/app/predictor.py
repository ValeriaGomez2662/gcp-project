import pandas as pd
from .features import build_common_features, enrich_warm_features

def is_warm(payload: dict) -> bool:
    return payload.get("tasa_compra_historica") is not None

def predict_score(payload: dict, artifacts: dict):
    model_stats = artifacts["model_stats"]
    model_cold = artifacts["model_cold"]
    model_warm = artifacts["model_warm"]
    scaler_rfm = artifacts["scaler_rfm"]
    kmeans_rfm = artifacts["kmeans_rfm"]

    df = build_common_features(payload)

    if is_warm(payload):
        for k, v in payload.items():
            if k not in df.columns:
                df[k] = v

        df = enrich_warm_features(df)

        # segmento RFM
        rfm = pd.DataFrame([{
            "recencia": df["dias_desde_ultima_compra"].iloc[0],
            "frecuencia": df["compras_acumuladas"].iloc[0],
            "valor": df["compras_acumuladas"].iloc[0],  # proxy simple
        }])

        rfm_scaled = scaler_rfm.transform(rfm)
        df["seg_enc"] = kmeans_rfm.predict(rfm_scaled)[0]

        cols = model_stats["fcols_warm"]
        score = float(model_warm.predict_proba(df[cols])[:, 1][0])
        threshold = model_stats["umbral_warm"]
        tipo = "warm"

    else:
        cols = model_stats["fcols_cold"]
        score = float(model_cold.predict_proba(df[cols])[:, 1][0])
        threshold = model_stats["umbral_cold"]
        tipo = "cold"

    prioridad = "ALTA" if score >= 0.60 else "MEDIA" if score >= 0.40 else "BAJA"
    pred = int(score >= threshold)

    return {
        "tipo_modelo": tipo,
        "score_propension": round(score, 4),
        "compra_predicha": pred,
        "prioridad": prioridad
    }