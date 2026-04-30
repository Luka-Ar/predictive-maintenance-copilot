# Predictive Maintenance Copilot

A hybrid AI predictive maintenance MVP that estimates machine failure risk from sensor data using machine learning and enhances interpretability with local Gemma (Ollama) explanations.

## 🎯 Overview

This project demonstrates a complete end-to-end system for predictive maintenance that combines:
- **Machine Learning** - RandomForest classifier trained on industrial sensor data
- **Risk Scoring** - Threshold-based probability predictions
- **Local LLM Integration** - Ollama Gemma for natural language explanations
- **Modern Web UI** - Real-time prediction dashboard with history tracking
- **Clean Architecture** - Modular FastAPI backend + Next.js React frontend

## ✨ Features

- 🤖 **ML-Based Predictions** - RandomForest model with configurable failure probability threshold
- 💬 **Explainable AI** - Local Gemma LLM generates interpretable explanations for each prediction
- 📊 **Real-time Dashboard** - Next.js UI for submitting predictions and viewing results
- 📈 **Prediction History** - SQLite database stores all predictions with timestamps
- 🎨 **Modern UI** - Tailwind CSS styling with visual risk indicators (Low/High Risk badges)
- ⚡ **Fast API** - FastAPI backend with CORS support for seamless frontend integration
- 🔄 **End-to-End** - Complete workflow from sensor input → ML model → LLM explanation → UI display

## 🏗️ Architecture

```
Sensor Input (Temperature, RPM, Torque, Tool Wear, etc.)
    ↓
FastAPI Backend
    ├─ Feature Preprocessing
    ├─ RandomForest ML Model (threshold-based)
    ├─ Failure Probability Calculation
    └─ Ollama Gemma LLM for Explanation
    ↓
SQLite History Database
    ↓
Next.js React Frontend Dashboard
    └─ Risk Indicators, Explanations, History View
```

## 📦 Tech Stack

**Backend:**
- Python 3.13
- FastAPI + Uvicorn
- scikit-learn (RandomForest)
- SQLite3
- Requests (Ollama API)
- Joblib (model serialization)

**Frontend:**
- Next.js 16.2 (React 19)
- TypeScript
- Tailwind CSS
- React Hooks for state management

**ML & LLM:**
- Ollama (local LLM runtime)
- Gemma 4 (language model)
- scikit-learn (model training)

**Data:**
- pandas / NumPy (data processing)
- UCI AI4I2020 Dataset (industrial maintenance data)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama installed and running

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn api.main:app --reload
# Server will run on http://127.0.0.1:8000
```

### 2. Frontend Setup

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend will run on http://localhost:3000
```

### 3. LLM Setup

```bash
# Pull Gemma 4 model (one-time)
ollama pull gemma4:e2b

# Run Ollama service
ollama run gemma4:e2b
# LLM will be available at localhost:11434
```

### 4. Train ML Model

```bash
# From project root
python training/train_baseline.py
# This trains the RandomForest model on the AI4I2020 dataset
# Outputs: models/failure_model.joblib, models/feature_columns.joblib
```

## 📖 Project Structure

```
predictive-maintenance-copilot/
├── api/                        # FastAPI backend
│   └── main.py                # API routes, model serving, Ollama integration
├── training/                  # ML training pipeline
│   └── train_baseline.py     # RandomForest training script
├── models/                    # Trained model artifacts
│   ├── failure_model.joblib  # Serialized model
│   └── feature_columns.joblib # Feature metadata
├── data/                      # Dataset directory
│   └── ai4i2020.csv         # UCI dataset (not in repo)
├── notebooks/                # Jupyter exploration
│   └── 01_explore.py        # Data exploration notebook
├── web/                       # Next.js frontend
│   ├── src/app/
│   │   └── page.tsx         # Main React component
│   ├── package.json
│   └── tsconfig.json
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .gitignore               # Git ignore rules
```

## 🔧 API Endpoints

### POST /predict
Submit machine sensor readings for failure risk prediction.

**Request:**
```json
{
  "Type": "M",
  "Air_temperature_K": 300.5,
  "Process_temperature_K": 310.2,
  "Rotational_speed_rpm": 1500,
  "Torque_Nm": 40.5,
  "Tool_wear_min": 5
}
```

**Response:**
```json
{
  "prediction": 0,
  "failure_probability": 0.15,
  "explanation": "The current operating parameters indicate normal conditions..."
}
```

### GET /history
Retrieve prediction history (latest 20 predictions).

**Response:**
```json
[
  {
    "id": 1,
    "created_at": "2026-04-30T11:05:26.081848",
    "machine_type": "M",
    "failure_probability": 0.15,
    "explanation": "..."
  }
]
```

### DELETE /history
Clear all prediction history from the database.

## 🧠 Model Details

- **Algorithm:** RandomForest Classifier (n_estimators=200)
- **Features:** Air/Process Temperature, Rotational Speed, Torque, Tool Wear, Machine Type
- **Threshold:** 0.3 (failure probability)
- **Training Data:** UCI AI4I2020 (predictive maintenance dataset)
- **Performance:** ~98% accuracy on test set

## 📝 Notes

- **Prototype/MVP Status:** This is an educational demonstration of hybrid AI architecture, not production-ready for safety-critical systems
- **Local LLM:** Uses Ollama for local inference - no cloud dependencies or API keys required
- **Educational Purpose:** Designed to showcase full-stack AI development from ML training through LLM integration to modern web UI
- **Real-World Deployment:** Before production use in actual industrial settings, validate with domain experts and real operational data

## 🎓 Learning Resources

This project demonstrates:
- Building end-to-end ML systems
- Integrating local LLMs for explainability
- FastAPI backend development
- React/Next.js frontend patterns
- Database persistence
- API design and documentation

## 📸 Screenshots

See `screenshots/` folder for dashboard examples:
- Main prediction dashboard
- Low-risk prediction example
- High-risk prediction example
- Prediction history view

## 🔗 Links

- **GitHub:** https://github.com/Luka-Ar/predictive-maintenance-copilot
- **Dataset:** UCI AI4I2020 Predictive Maintenance Dataset
- **Ollama:** https://ollama.ai
- **Gemma:** Google's open-source language model

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

Created as a demonstration of hybrid AI architecture combining machine learning with local LLM integration for enhanced interpretability.

---

**Ready to explore predictive AI? Start with the Quick Start guide above!**
