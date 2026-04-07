from google.cloud import bigquery
from .config import PROJECT_ID, BQ_DATASET, BQ_VIEW

bq = bigquery.Client(project=PROJECT_ID)

VIEW_FULL_NAME = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_VIEW}"

def top_clients(limit: int = 10):
    sql = f"""
    SELECT *
    FROM `{VIEW_FULL_NAME}`
    ORDER BY score_propension DESC
    LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    rows = bq.query(sql, job_config=job_config).result()
    return [dict(row) for row in rows]

def query_sql(sql: str):
    rows = bq.query(sql).result()
    return [dict(row) for row in rows]

def filter_clients(
    segmento: str = None,
    prioridad: str = None,
    score_min: float = None,
    dias_max: float = None,
    limit: int = 10
):
    where_clauses = []
    params = []

    if segmento:
        where_clauses.append("segmento = @segmento")
        params.append(bigquery.ScalarQueryParameter("segmento", "STRING", segmento))

    if prioridad:
        where_clauses.append("prioridad = @prioridad")
        params.append(bigquery.ScalarQueryParameter("prioridad", "STRING", prioridad))

    if score_min is not None:
        where_clauses.append("score_propension >= @score_min")
        params.append(bigquery.ScalarQueryParameter("score_min", "FLOAT64", score_min))

    if dias_max is not None:
        where_clauses.append("dias_desde_ultima_compra <= @dias_max")
        params.append(bigquery.ScalarQueryParameter("dias_max", "FLOAT64", dias_max))

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
    SELECT *
    FROM `{VIEW_FULL_NAME}`
    {where_sql}
    ORDER BY score_propension DESC
    LIMIT @limit
    """

    params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    rows = bq.query(sql, job_config=job_config).result()
    return [dict(row) for row in rows]