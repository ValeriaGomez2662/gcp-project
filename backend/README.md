# 🚀 Propensión de Compra con IA

Proyecto end-to-end que combina:
- Machine Learning (Cold/Warm)
- FastAPI backend
- BigQuery
- Vertex AI (Gemini)
- Streamlit frontend

## 🧠 Arquitectura
Frontend → Backend → BigQuery + GCS + Vertex AI

## ⚙️ Cómo ejecutar

### Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

### Frontend
cd frontend
streamlit run app.py

## 🔐 Notas
No se incluyen credenciales ni datos sensibles.