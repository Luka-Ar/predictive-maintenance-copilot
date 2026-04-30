# Detailed Setup Guide

Complete step-by-step instructions for setting up the Predictive Maintenance Copilot on your machine.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **Node.js 18 or higher** ([Download](https://nodejs.org/))
- **Ollama** ([Download](https://ollama.ai))
- **Git** ([Download](https://git-scm.com/))

## Step 1: Clone the Repository

```bash
git clone https://github.com/Luka-Ar/predictive-maintenance-copilot.git
cd predictive-maintenance-copilot
```

## Step 2: Set Up the Backend

### 2.1 Create Virtual Environment

Create an isolated Python environment for the project:

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt.

### 2.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- uvicorn (server)
- scikit-learn (machine learning)
- pandas, numpy (data processing)
- joblib (model persistence)
- requests (HTTP client)

### 2.3 Verify Installation

```bash
python -c "from api.main import app; print('✓ Backend ready')"
```

## Step 3: Set Up the Frontend

### 3.1 Install Frontend Dependencies

Navigate to the web directory:

```bash
cd web
npm install
```

This installs:
- Next.js 16 (React framework)
- React 19 (UI library)
- Tailwind CSS (styling)
- TypeScript (type safety)

### 3.2 Verify Installation

```bash
npm run lint
```

Should complete without errors.

## Step 4: Set Up Ollama and Gemma

### 4.1 Install Ollama

Download and install from [ollama.ai](https://ollama.ai)

### 4.2 Pull Gemma Model

```bash
ollama pull gemma4:e2b
```

This downloads the Gemma 4 model (~7GB). First time only.

### 4.3 Verify Ollama Installation

```bash
ollama list
```

You should see `gemma4:e2b` in the list.

## Step 5: Train the ML Model (Optional)

If you want to regenerate the trained model:

```bash
# From project root (make sure .venv is activated)
python training/train_baseline.py
```

This trains a RandomForest model on the AI4I2020 dataset and saves artifacts to `models/`.

**Note:** The model is already trained and included in the repository, so this step is optional.

## Step 6: Run the Complete System

### Terminal 1: Start Ollama

```bash
ollama run gemma4:e2b
```

Leave this running - it starts the LLM service at `localhost:11434`.

### Terminal 2: Start Backend API

```bash
# Make sure you're in the project root
# Make sure .venv is activated
cd path/to/predictive-maintenance-copilot
source .venv/bin/activate  # (or .venv\Scripts\activate on Windows)
uvicorn api.main:app --reload
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Terminal 3: Start Frontend

```bash
cd web
npm run dev
```

You should see:
```
▲ Next.js 16.2.4
  ✓ Ready in 1.2s
```

Open your browser to `http://localhost:3000`

## Step 7: Test the System

### 7.1 Submit a Prediction

1. Go to `http://localhost:3000`
2. Fill in the prediction form with sensor values
3. Click "Predict"
4. View the failure risk and LLM explanation

### 7.2 Check History

Scroll down to see all your predictions with timestamps.

### 7.3 API Test

Make a direct API call:

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "M",
    "Air_temperature_K": 305,
    "Process_temperature_K": 315,
    "Rotational_speed_rpm": 1500,
    "Torque_Nm": 40,
    "Tool_wear_min": 25
  }'
```

## Troubleshooting

### Backend Won't Start

**Error:** `port 8000 already in use`
- Solution: `lsof -i :8000` (macOS/Linux) or `netstat -ano | findstr :8000` (Windows)
- Kill the process or use a different port: `uvicorn api.main:app --port 8001`

**Error:** `ModuleNotFoundError`
- Solution: Make sure `.venv` is activated

### Frontend Won't Start

**Error:** `npm: command not found`
- Solution: Install Node.js from https://nodejs.org/

**Error:** `port 3000 already in use`
- Solution: Use a different port: `npm run dev -- -p 3001`

### Ollama Won't Connect

**Error:** `Failed to connect to Ollama at localhost:11434`
- Solution: Make sure `ollama run gemma4:e2b` is running in another terminal
- Try `curl localhost:11434` to verify Ollama is running

### Database Issues

**Error:** `database is locked`
- Solution: Make sure only one instance of the backend is running

**To reset the database:**
```bash
rm predictions.db
```

The database will be recreated on next API call.

## Project Structure

```
predictive-maintenance-copilot/
├── api/                           # Backend FastAPI app
│   └── main.py                   # API endpoints and ML serving
├── training/                     # ML training scripts
│   └── train_baseline.py        # RandomForest training
├── models/                       # Trained model artifacts
│   ├── failure_model.joblib     # Serialized model
│   └── feature_columns.joblib   # Feature metadata
├── web/                          # Frontend Next.js app
│   ├── src/app/page.tsx         # React UI component
│   ├── package.json
│   └── tailwind.config.ts
├── data/                         # Datasets (not in repo)
├── notebooks/                    # Jupyter exploration
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview
├── API.md                        # API documentation
├── SETUP.md                      # This file
└── CONTRIBUTING.md               # Contribution guidelines
```

## Next Steps

- Read [API.md](API.md) for detailed API documentation
- See [README.md](README.md) for project overview
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute improvements
- Review [training/train_baseline.py](training/train_baseline.py) to understand ML pipeline

## Getting Help

- Check existing [GitHub Issues](https://github.com/Luka-Ar/predictive-maintenance-copilot/issues)
- Review the [README.md](README.md) for more information
- Examine the code comments for implementation details

---

**You're all set! Happy predictive maintenance! 🚀**
