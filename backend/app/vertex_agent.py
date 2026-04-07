import os
import json
from google import genai
from google.genai import types

from .config import PROJECT_ID, LOCATION, BQ_DATASET, BQ_VIEW
from .bq_tools import query_sql

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

MODEL_NAME = "gemini-2.5-flash"
VIEW_FULL_NAME = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_VIEW}"

SYSTEM_PROMPT = f"""
Eres un asistente comercial de Ferreycorp.
Tu trabajo es ayudar al negocio a consultar clientes con propensión de compra.

La fuente oficial de datos es la vista:
`{VIEW_FULL_NAME}`

Columnas disponibles:
- id_cliente
- segmento
- score_propension
- compra_predicha
- tasa_compra_historica
- dias_desde_ultima_compra
- frecuencia_compras_30d
- bucket
- prioridad
- canal_sugerido

Reglas:
- Nunca inventes datos
- Si el usuario solo saluda, responde normal
- Si el usuario pide clientes, rankings, filtros o explicaciones, genera una consulta SQL
- Usa SIEMPRE SELECT
- Usa SIEMPRE la vista completa indicada
- LIMIT por defecto: 10
- Responde en español y de forma ejecutiva
"""

PLANNER_PROMPT = f"""
Convierte la consulta del usuario en un JSON válido.

Responde SOLO con JSON.
Sin markdown.
Sin explicación adicional.

Formato exacto:
{{
  "needs_query": true o false,
  "sql": "consulta SQL o cadena vacía",
  "reason": "explicación corta"
}}

Reglas SQL:
- usar exclusivamente esta vista: `{VIEW_FULL_NAME}`
- solo SELECT
- si el usuario pide top clientes: ORDER BY score_propension DESC
- si el usuario pregunta "a quién llamar hoy", prioriza:
  score_propension alto, dias_desde_ultima_compra <= 15, prioridad = 'ALTA'
- si el usuario pide "baja frecuencia", interpreta como:
  frecuencia_compras_30d <= 1
- si el usuario pide "alta recencia", interpreta como:
  dias_desde_ultima_compra >= 30
- si el usuario no especifica límite, usa LIMIT 10
- si solo saluda, no hagas query
- columnas válidas:
  id_cliente, segmento, score_propension, compra_predicha,
  tasa_compra_historica, dias_desde_ultima_compra,
  frecuencia_compras_30d, bucket, prioridad, canal_sugerido
"""

def extract_text(resp):
    txt = getattr(resp, "text", None)
    if txt:
        return txt.strip()

    texts = []
    for cand in getattr(resp, "candidates", []) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                texts.append(part_text)

    return "\n".join(texts).strip() if texts else ""

def generate_plan(user_message: str):
    prompt = f"""
{SYSTEM_PROMPT}

{PLANNER_PROMPT}

Consulta del usuario:
{user_message}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=500
        )
    )

    text = extract_text(response)
    print("PLAN RAW:", text)

    try:
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"Error parseando JSON del planner. Respuesta cruda: {text}") from e

def answer_with_data(user_message: str, rows):
    prompt = f"""
{SYSTEM_PROMPT}

Pregunta original del usuario:
{user_message}

Resultados obtenidos:
{json.dumps(rows, ensure_ascii=False, indent=2)}

Responde:
- en español
- de forma ejecutiva
- resumiendo hallazgos clave
- incluyendo recomendación comercial
- si hay lista de clientes, menciona por qué priorizarlos
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=700
        )
    )

    return extract_text(response)

def safe_sql(sql: str):
    sql_clean = sql.strip().rstrip(";")
    sql_lower = sql_clean.lower()

    if not sql_lower.startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT.")

    forbidden = ["insert ", "update ", "delete ", "drop ", "alter ", "create ", "merge ", "truncate "]
    if any(word in sql_lower for word in forbidden):
        raise ValueError("La consulta contiene operaciones no permitidas.")

    if VIEW_FULL_NAME.lower() not in sql_lower:
        raise ValueError(f"La consulta debe usar la vista `{VIEW_FULL_NAME}`.")

    valid_cols = [
        "id_cliente", "segmento", "score_propension", "compra_predicha",
        "tasa_compra_historica", "dias_desde_ultima_compra",
        "frecuencia_compras_30d", "bucket", "prioridad", "canal_sugerido"
    ]

    return sql_clean

def agente_chat(user_message: str):
    msg = user_message.lower()

    if "baja frecuencia" in msg and "alta recencia" in msg:
        sql = f"""
        SELECT *
        FROM `{VIEW_FULL_NAME}`
        WHERE frecuencia_compras_30d <= 1
        AND dias_desde_ultima_compra >= 30
        ORDER BY dias_desde_ultima_compra DESC
        LIMIT 10
        """
        rows = query_sql(sql)
        answer = answer_with_data(user_message, rows)
        return {
            "answer": answer,
            "tool_calls": [
                {
                    "tool": "query_scores",
                    "reason": "Regla de negocio predefinida: baja frecuencia y alta recencia",
                    "sql": sql,
                    "rows_returned": len(rows)
                }
            ],
            "data": rows
        }

    plan = generate_plan(user_message)

    needs_query = plan.get("needs_query", False)
    sql = plan.get("sql", "")
    reason = plan.get("reason", "")

    if not needs_query:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"{SYSTEM_PROMPT}\n\nUsuario: {user_message}",
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=300
            )
        )
        return {
            "answer": extract_text(response),
            "tool_calls": []
        }

    sql = safe_sql(sql)
    rows = query_sql(sql)
    answer = answer_with_data(user_message, rows)

    return {
        "answer": answer,
        "tool_calls": [
            {
                "tool": "query_scores",
                "reason": reason,
                "sql": sql,
                "rows_returned": len(rows)
            }
        ],
        "data": rows
    }