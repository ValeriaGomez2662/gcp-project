import pandas as pd

def build_common_features(payload: dict) -> pd.DataFrame:
    df = pd.DataFrame([payload])

    price_cols = [f"precio_marca_{i}" for i in range(1, 6)]
    promo_cols = [f"promo_marca_{i}" for i in range(1, 6)]

    df["precio_minimo_dia"] = df[price_cols].min(axis=1)
    df["precio_promedio_dia"] = df[price_cols].mean(axis=1)
    df["rango_precios_dia"] = df[price_cols].max(axis=1) - df[price_cols].min(axis=1)
    df["num_promos_activas"] = df[promo_cols].sum(axis=1)

    return df

def enrich_warm_features(df: pd.DataFrame) -> pd.DataFrame:
    marca = int(df["ultima_marca_comprada"].iloc[0] or 0)

    if marca > 0:
        df["precio_ultima_marca"] = df[f"precio_marca_{marca}"]
        df["promo_sobre_ultima"] = df[f"promo_marca_{marca}"]
        df["precio_relativo"] = df["precio_ultima_marca"] / df["precio_minimo_dia"]
    else:
        df["precio_ultima_marca"] = df["precio_promedio_dia"]
        df["promo_sobre_ultima"] = 0
        df["precio_relativo"] = 1.0

    dia = float(df["dia_visita"].iloc[0])
    df["trimestre"] = ((dia - 1) // 182) + 1
    df["semana"] = ((dia - 1) // 7) + 1

    return df