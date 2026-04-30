"""FastAPI service for Predictive Maintenance failure prediction."""

from pathlib import Path
import sqlite3
from datetime import datetime
from typing import Literal

import joblib
import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create the FastAPI application.
app = FastAPI(title="Predictive Maintenance Copilot API")

# Allow local frontend apps to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load saved model artifacts.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "failure_model.joblib"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "models" / "feature_columns.joblib"
DB_PATH = PROJECT_ROOT / "predictions.db"

model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(FEATURE_COLUMNS_PATH)

# Decision threshold for classifying failures.
THRESHOLD = 0.3


def init_db() -> None:
    """Create prediction history table if it does not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                machine_type TEXT,
                air_temperature_k REAL,
                process_temperature_k REAL,
                rotational_speed_rpm REAL,
                torque_nm REAL,
                tool_wear_min REAL,
                prediction INTEGER,
                failure_probability REAL,
                explanation TEXT
            )
            """
        )
        conn.commit()


def save_prediction_history(
    payload: "PredictionInput",
    prediction: int,
    failure_probability: float,
    explanation: str,
) -> None:
    """Insert one prediction row into SQLite history."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO prediction_history (
                created_at,
                machine_type,
                air_temperature_k,
                process_temperature_k,
                rotational_speed_rpm,
                torque_nm,
                tool_wear_min,
                prediction,
                failure_probability,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                payload.Type,
                payload.Air_temperature_K,
                payload.Process_temperature_K,
                payload.Rotational_speed_rpm,
                payload.Torque_Nm,
                payload.Tool_wear_min,
                prediction,
                failure_probability,
                explanation,
            ),
        )
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    """Initialize local SQLite database on app startup."""
    init_db()


class PredictionInput(BaseModel):
    """Input schema for one machine record."""

    Type: Literal["L", "M", "H"]
    Air_temperature_K: float
    Process_temperature_K: float
    Rotational_speed_rpm: float
    Torque_Nm: float
    Tool_wear_min: float


def generate_llm_explanation(
    input_data: PredictionInput, probability: float, prediction: int
) -> str:
    """Generate a short explanation using a local Ollama Gemma model."""
    print("generate_llm_explanation called")

    high_torque = "yes" if input_data.Torque_Nm > 60 else "no"
    high_tool_wear = "yes" if input_data.Tool_wear_min > 150 else "no"
    large_temp_diff = (
        "yes"
        if (input_data.Process_temperature_K - input_data.Air_temperature_K) > 10
        else "no"
    )
    risk_text = (
        "The ML system predicted elevated failure risk."
        if prediction == 1
        else "The ML system predicted low failure risk."
    )

    prompt = f"""
You are an industrial maintenance assistant.

Given these machine values:
- Type: {input_data.Type}
- Air temperature: {input_data.Air_temperature_K} K
- Process temperature: {input_data.Process_temperature_K} K
- Rotational speed: {input_data.Rotational_speed_rpm} rpm
- Torque: {input_data.Torque_Nm} Nm
- Tool wear: {input_data.Tool_wear_min} min

Observed conditions:
- High torque: {high_torque}
- High tool wear: {high_tool_wear}
- Large temperature difference: {large_temp_diff}

{risk_text}

Write a short explanation in practical engineering language.
Do not mention probability unless necessary.
Do not invent faults.
Use only the given values.
Keep the answer under 3 sentences.
"""

    # Handle local LLM connection issues gracefully when Ollama is not running.
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:e2b",
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 120,
                },
            },
            timeout=180,
        )

        if response.status_code != 200:
            return f"Ollama error: {response.text}"

        raw_json = response.json()

        explanation = raw_json.get("response", "").strip()
        if not explanation:
            return "LLM returned an empty explanation."

        return explanation
    except requests.RequestException as exc:
        return f"LLM error: {exc}"
    except ValueError:
        return "LLM explanation unavailable (invalid response from Ollama)."


@app.get("/")
def read_root() -> dict:
    """Basic welcome endpoint to confirm API status."""
    return {"message": "Predictive Maintenance API running"}


@app.get("/history")
def get_history() -> list[dict]:
    """Return the 20 most recent prediction records."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                machine_type,
                air_temperature_k,
                process_temperature_k,
                rotational_speed_rpm,
                torque_nm,
                tool_wear_min,
                prediction,
                failure_probability,
                explanation
            FROM prediction_history
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

    return [dict(row) for row in rows]


@app.delete("/history")
def clear_history() -> dict:
    """Delete all prediction history rows."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM prediction_history")
        conn.commit()

    return {"message": "History cleared", "deleted_rows": cursor.rowcount}


@app.post("/predict")
def predict_failure(payload: PredictionInput) -> dict:
    """Predict machine failure probability and class label."""

    # Map API input names to the feature names used during training.
    row = {
        "Air temperature [K]": payload.Air_temperature_K,
        "Process temperature [K]": payload.Process_temperature_K,
        "Rotational speed [rpm]": payload.Rotational_speed_rpm,
        "Torque [Nm]": payload.Torque_Nm,
        "Tool wear [min]": payload.Tool_wear_min,
        # One-hot encoding for Type where H is the default (0, 0).
        "Type_L": 1 if payload.Type == "L" else 0,
        "Type_M": 1 if payload.Type == "M" else 0,
    }

    # Convert to DataFrame so we can align columns with the trained model.
    input_df = pd.DataFrame([row])

    # Ensure all expected feature columns exist; fill missing with 0.
    for col in feature_columns:
        if col not in input_df.columns:
            input_df[col] = 0

    # Keep only the feature columns in the exact training order.
    input_df = input_df[feature_columns]

    # Predict class-1 probability (machine failure).
    failure_probability = float(model.predict_proba(input_df)[0][1])
    prediction = int(failure_probability >= THRESHOLD)
    explanation = generate_llm_explanation(payload, failure_probability, prediction)

    # Save prediction input/output to local SQLite history.
    save_prediction_history(payload, prediction, failure_probability, explanation)

    return {
        "prediction": prediction,
        "failure_probability": failure_probability,
        "explanation": explanation,
    }
