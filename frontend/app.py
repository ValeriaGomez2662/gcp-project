import streamlit as st
import requests
import pandas as pd
import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Ferreycorp Propensión - Valeria Gòmez",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Ferreycorp - Propensión de Compra")
st.caption("Frontend Streamlit conectado al backend FastAPI . Milagros Valeria Gòmez Salcedo")

# Sidebar
st.sidebar.title("Navegación")
page = st.sidebar.radio(
    "Ir a:",
    ["Dashboard", "Chat", "Predicción"]
)

# -------------------------
# Helpers
# -------------------------
def get_top_clients(limit=10):
    r = requests.get(f"{BACKEND_URL}/top-clients", params={"limit": limit}, timeout=60)
    r.raise_for_status()
    return r.json()["rows"]

def post_chat(message: str):
    r = requests.post(
        f"{BACKEND_URL}/chat",
        json={"message": message},
        timeout=120
    )
    r.raise_for_status()
    return r.json()

def post_predict(payload: dict):
    r = requests.post(
        f"{BACKEND_URL}/predict",
        json=payload,
        timeout=120
    )
    r.raise_for_status()
    return r.json()

def post_filter_clients(payload: dict):
    r = requests.post(
        f"{BACKEND_URL}/filter-clients",
        json=payload,
        timeout=120
    )
    r.raise_for_status()
    return r.json()["rows"]

# -------------------------
# DASHBOARD
# -------------------------
if page == "Dashboard":
    st.subheader("Top clientes")

    col1, col2 = st.columns([1, 3])

    with col1:
        limit = st.number_input("Cantidad de clientes", min_value=1, max_value=50, value=10)

        segmento = st.selectbox(
            "Segmento",
            options=["Todos", "Alto", "Medio-Alto", "Medio-Bajo", "Bajo"]
        )

        prioridad = st.selectbox(
            "Prioridad",
            options=["Todas", "ALTA", "MEDIA", "BAJA"]
        )

        score_min = st.slider("Score mínimo", 0.0, 1.0, 0.4, 0.01)
        dias_max = st.number_input("Máx. días desde última compra", min_value=0, max_value=365, value=30)

        use_filter = st.checkbox("Usar filtros avanzados", value=False)

    with col2:
        try:
            if use_filter:
                payload = {
                    "segmento": None if segmento == "Todos" else segmento,
                    "prioridad": None if prioridad == "Todas" else prioridad,
                    "score_min": score_min,
                    "dias_max": dias_max,
                    "limit": int(limit)
                }
                rows = post_filter_clients(payload)
            else:
                rows = get_top_clients(limit=int(limit))

            df = pd.DataFrame(rows)

            if not df.empty:
                k1, k2, k3 = st.columns(3)
                k1.metric("Clientes mostrados", len(df))
                if "score_propension" in df.columns:
                    k2.metric("Score promedio", f"{df['score_propension'].mean():.3f}")
                if "prioridad" in df.columns:
                    k3.metric("Prioridad ALTA", int((df["prioridad"] == "ALTA").sum()))

                st.dataframe(df, use_container_width=True)

                if "segmento" in df.columns:
                    st.subheader("Distribución por segmento")
                    st.bar_chart(df["segmento"].value_counts())

                if "prioridad" in df.columns:
                    st.subheader("Distribución por prioridad")
                    st.bar_chart(df["prioridad"].value_counts())
            else:
                st.warning("No se encontraron clientes con esos criterios.")
        except Exception as e:
            st.error(f"Error cargando dashboard: {e}")

# -------------------------
# CHAT
# -------------------------
elif page == "Chat":
    st.subheader("Agente conversacional")
    
    st.info("💡 Puedes hacer preguntas como: '¿A quién llamar hoy?', 'top clientes', 'clientes prioridad alta'")

    st.markdown("### ⚡ Preguntas sugeridas")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📞 ¿A quién debería llamar hoy?"):
            st.session_state.quick_question = "¿A quién debería llamar hoy?"

        if st.button("🔥 Top 10 clientes con mayor propensión"):
            st.session_state.quick_question = "Dame los 10 clientes con mayor propensión"

    with col2:
        if st.button("📊 Clientes prioridad ALTA"):
            st.session_state.quick_question = "Muéstrame clientes con prioridad ALTA"

        if st.button("📉 Clientes con riesgo de abandono"):
            st.session_state.quick_question = "Dame clientes con baja frecuencia y alta recencia"

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input("Escribe tu consulta...")

    # Si el usuario hizo click en botón
    if "quick_question" in st.session_state:
        prompt = st.session_state.quick_question
        del st.session_state.quick_question

    if prompt:
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = post_chat(prompt)
            answer = response.get("answer", "Sin respuesta")

            with st.chat_message("assistant"):
                st.markdown(answer)

                tool_calls = response.get("tool_calls", [])
                if tool_calls:
                    with st.expander("Ver trazabilidad del agente"):
                        st.json(tool_calls)

                data = response.get("data", None)
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"Error en chat: {e}")

# -------------------------
# PREDICCIÓN
# -------------------------
elif page == "Predicción":
    st.subheader("Simular nueva visita")

    st.markdown("Completa los datos para estimar la propensión de compra.")

    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            edad = st.number_input("Edad", 18, 100, 45)
            genero = st.number_input("Género", 0, 5, 1)
            estado_civil = st.number_input("Estado civil", 0, 5, 1)
            nivel_educacion = st.number_input("Nivel educación", 0, 10, 2)
            ingreso_anual = st.number_input("Ingreso anual", 0.0, 1000000.0, 120000.0)
            ocupacion = st.number_input("Ocupación", 0, 20, 1)

        with c2:
            precio_marca_1 = st.number_input("Precio marca 1", 0.0, 100.0, 1.39)
            precio_marca_2 = st.number_input("Precio marca 2", 0.0, 100.0, 1.88)
            precio_marca_3 = st.number_input("Precio marca 3", 0.0, 100.0, 2.01)
            precio_marca_4 = st.number_input("Precio marca 4", 0.0, 100.0, 2.17)
            precio_marca_5 = st.number_input("Precio marca 5", 0.0, 100.0, 2.67)

        with c3:
            promo_marca_1 = st.number_input("Promo marca 1", 0, 1, 0)
            promo_marca_2 = st.number_input("Promo marca 2", 0, 1, 1)
            promo_marca_3 = st.number_input("Promo marca 3", 0, 1, 0)
            promo_marca_4 = st.number_input("Promo marca 4", 0, 1, 0)
            promo_marca_5 = st.number_input("Promo marca 5", 0, 1, 0)

        st.markdown("### Historial opcional (warm start)")
        use_warm = st.checkbox("Tengo historial del cliente", value=False)

        ultima_marca_comprada = None
        ultima_cantidad_comprada = None
        dias_desde_ultima_compra = None
        compras_acumuladas = None
        tasa_compra_historica = None
        frecuencia_compras_30d = None
        compras_ultimas_3_visitas = None
        habia_comprado_ayer = None
        dia_visita = 730

        if use_warm:
            wc1, wc2, wc3 = st.columns(3)
            with wc1:
                ultima_marca_comprada = st.number_input("Última marca comprada", 0, 5, 2)
                ultima_cantidad_comprada = st.number_input("Última cantidad comprada", 0, 20, 1)
                dias_desde_ultima_compra = st.number_input("Días desde última compra", 0.0, 365.0, 10.0)

            with wc2:
                compras_acumuladas = st.number_input("Compras acumuladas", 0.0, 500.0, 12.0)
                tasa_compra_historica = st.number_input("Tasa compra histórica", 0.0, 1.0, 0.34)
                frecuencia_compras_30d = st.number_input("Frecuencia compras 30d", 0.0, 100.0, 3.0)

            with wc3:
                compras_ultimas_3_visitas = st.number_input("Compras últimas 3 visitas", 0.0, 3.0, 2.0)
                habia_comprado_ayer = st.number_input("Había comprado ayer", 0, 1, 1)
                dia_visita = st.number_input("Día visita", 1, 10000, 730)

        submitted = st.form_submit_button("Predecir")

    if submitted:
        payload = {
            "edad": edad,
            "genero": genero,
            "estado_civil": estado_civil,
            "nivel_educacion": nivel_educacion,
            "ingreso_anual": ingreso_anual,
            "ocupacion": ocupacion,
            "precio_marca_1": precio_marca_1,
            "precio_marca_2": precio_marca_2,
            "precio_marca_3": precio_marca_3,
            "precio_marca_4": precio_marca_4,
            "precio_marca_5": precio_marca_5,
            "promo_marca_1": promo_marca_1,
            "promo_marca_2": promo_marca_2,
            "promo_marca_3": promo_marca_3,
            "promo_marca_4": promo_marca_4,
            "promo_marca_5": promo_marca_5,
        }

        if use_warm:
            payload.update({
                "ultima_marca_comprada": ultima_marca_comprada,
                "ultima_cantidad_comprada": ultima_cantidad_comprada,
                "dias_desde_ultima_compra": dias_desde_ultima_compra,
                "compras_acumuladas": compras_acumuladas,
                "tasa_compra_historica": tasa_compra_historica,
                "frecuencia_compras_30d": frecuencia_compras_30d,
                "compras_ultimas_3_visitas": compras_ultimas_3_visitas,
                "habia_comprado_ayer": habia_comprado_ayer,
                "dia_visita": dia_visita
            })

        try:
            result = post_predict(payload)

            st.success("Predicción generada")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tipo modelo", result.get("tipo_modelo", "-"))
            c2.metric("Score", result.get("score_propension", "-"))
            c3.metric("Predicción", result.get("compra_predicha", "-"))
            c4.metric("Prioridad", result.get("prioridad", "-"))

            st.json(result)

        except Exception as e:
            st.error(f"Error en predicción: {e}")