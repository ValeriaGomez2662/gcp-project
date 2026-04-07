# 🎯 Modelo de Propensión de Compra con IA Conversacional

> Sistema predictivo end-to-end desplegado en Google Cloud Platform que predice si un cliente comprará en su próxima visita y permite al equipo comercial consultar esas predicciones en lenguaje natural.

## 🌐 Demo en producción

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | [propension-frontend-827318632719.us-east1.run.app](https://propension-frontend-827318632719.us-east1.run.app/) | Dashboard + Chat + Simulador |
| **Backend API** | [propension-backend-827318632719.us-east1.run.app/docs](https://propension-backend-827318632719.us-east1.run.app/docs) | Swagger UI interactivo |

---

## 🧠 Arquitectura

```
Usuario
  │
  ▼
Frontend (Streamlit · Cloud Run)
  │
  ▼
Backend (FastAPI · Cloud Run)
  │
  ├──► BigQuery ──────────► scores_clientes (500 clientes)
  │                         vw_scores_clientes (vista de negocio)
  │
  ├──► Cloud Storage ─────► modelo_cold_start.pkl
  │                         modelo_warm_start.pkl
  │                         scaler_rfm.pkl · kmeans_rfm.pkl
  │
  └──► Vertex AI ─────────► Gemini 2.5 Flash (agente conversacional)
```

---

## 🤖 Modelos de Machine Learning

El proyecto implementa una **arquitectura dual** para manejar dos escenarios distintos:

### Cold-Start — Primera visita (sin historial)

| Parámetro | Valor |
|-----------|-------|
| Algoritmo | Logistic Regression (L2, C=0.05) |
| Features | 6 demográficas + 14 de contexto de mercado |
| AUC | **0.746** (CV 5-fold) |
| Tasa basal | 10.6% |
| Umbral decisión | 0.15 |
| Cuándo se usa | `visit_rank = 0` |

> La LR se eligió sobre Random Forest porque con solo 500 primeras visitas y desbalance 8.4:1, es más estable y evita overfitting.

### Warm-Start — Clientes con historial

| Parámetro | Valor |
|-----------|-------|
| Algoritmo | Random Forest (400 árboles, max_depth=12) |
| Features | 35 variables: comportamiento + RFM + demografía + mercado |
| AUC | **0.685** (test temporal días 621–730) |
| Average Precision | 0.464 (1.8x el baseline) |
| Lift decil 10 | **2.34x** |
| Uplift llamadas | **+84%** vs contacto aleatorio |
| Umbral decisión | 0.43 |
| Cuándo se usa | `visit_rank ≥ 1` |

### Por qué Random Forest ganó sobre los competidores

| Modelo | AUC CV | AUC Test Temporal | Decisión |
|--------|--------|-------------------|----------|
| Logistic Regression | 0.731 | 0.708 | Baseline |
| **Random Forest** | **0.784** | **0.708** | **Champion ✓** |
| HistGradientBoosting | 0.816 | 0.666 | ❌ Descartado (-15pp caída) |
| CatBoost | 0.815 | 0.676 | Challenger |

> HistGBM fue descartado porque aunque brilló en CV (0.816), cayó a 0.666 en test temporal: **15 puntos de diferencia = overfitting severo**. El modelo se eligió por rendimiento en producción, no en laboratorio.

### Validación: backtesting rolling (no split aleatorio)

Los datos son longitudinales — usar `train_test_split` aleatorio mezcla información futura con el entrenamiento y produce AUC inflados que fallan en producción.

```
Ventana 1: Train días 1-365  →  Val días 366-450
Ventana 2: Train días 1-450  →  Val días 451-540
Ventana 3: Train días 1-540  →  Val días 541-620
Test FINAL: Train días 1-620  →  Test días 621-730 ← nunca visto antes
```

### Explicabilidad

- **Permutation Importance**: top predictores = `tasa_compra_historica`, `segmento_RFM`, `frecuencia_compras_30d`
- **SHAP**: valores individuales por predicción para explicar cada score al equipo comercial
- **Correlación tasa histórica ↔ score**: 0.814 — el modelo captura el principio intuitivo *"quien compró antes, comprará después"*

---

## 💬 Agente Conversacional

El sistema incorpora un agente basado en Gemini (Vertex AI) que permite:

- Consultar clientes con lenguaje natural
- Generar queries SQL automáticamente
- Explicar scores de propensión

Ejemplos:

- "¿A quién debería llamar hoy?"
- "Clientes con alta propensión y baja recencia"
- "Explícame el cliente 200000247"

El agente combina:
- LLM (Gemini)
- BigQuery (datos)
- Modelos ML (predicción)

## 🗂️ Estructura del repositorio

```
gcp-project/
│
├── README.md
├── .gitignore
│
├── notebooks/
│   ├── EDA_Propension_Compra01.ipynb
│   ├── Modelo_ColdWarm01.ipynb
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py
│
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
│
└── docs/
    ├── Documentación de la solución_ Milagros Gomez Salcedo .pdf
    └── Presentacion_Milagros Gomez Salcedo.pdf
```

---

## ⚙️ Cómo ejecutar localmente

### Requisitos previos

```bash
# Autenticación Google Cloud
gcloud auth application-default login
gcloud config set project PROJECT_ID
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Swagger disponible en: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

### Variables de entorno requeridas

| Variable | Descripción |
|----------|-------------|
| `GCP_PROJECT_ID` | ID del proyecto en Google Cloud |
| `GCS_BUCKET_NAME` | Bucket con los artefactos del modelo |
| `BIGQUERY_DATASET` | Dataset de BigQuery con los scores |
| `BACKEND_URL` | URL del backend (solo para el frontend) |

---

## 🏗️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Machine Learning | scikit-learn · Random Forest · Logistic Regression · SHAP |
| Datos | Google BigQuery · Cloud Storage |
| Backend | FastAPI · Python · Docker |
| Frontend | Streamlit · Docker |
| IA Conversacional | Gemini 2.5 Flash · Vertex AI |
| Despliegue | Cloud Run · Cloud Build · Artifact Registry |

---

## 📊 Resultados de negocio

| KPI | Valor |
|-----|-------|
| Lift decil 10 | 2.34x |
| Uplift llamadas comerciales (t=0.60) | +84% |
| Uplift CRM/alerta (t=0.50) | +65% |
| Clientes prioridad ALTA | 72 de 500 |
| Costo mensual GCP | ~$7/mes |

---

## ⚠️ Limitaciones

- Dataset pequeño (500 clientes)
- No incluye datos reales de CRM o campañas
- No hay feedback loop en producción
- El agente depende de prompts (no fine-tuned)
  
## 🔐 Notas de seguridad

- Los archivos `.pkl` del modelo **no están en el repositorio** (superan 25MB y contienen artefactos sensibles). Se almacenan en Google Cloud Storage y el backend los descarga al iniciar.
- Las credenciales, API keys y archivos `.env` están excluidos via `.gitignore`.
