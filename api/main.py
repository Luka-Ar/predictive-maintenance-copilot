"""FastAPI service for Predictive Maintenance failure prediction."""

from pathlib import Path
import sqlite3
from datetime import datetime
from typing import Literal

import joblib
import chromadb
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
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
RAG_COLLECTION = "industrial_knowledge"
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


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


def get_recent_history(limit: int = 3) -> list[sqlite3.Row]:
    """Return recent prediction history rows for trend analysis."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                air_temperature_k,
                process_temperature_k,
                torque_nm,
                tool_wear_min
            FROM prediction_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows


def get_rag_context(query: str, priority_sources: list[str] | None = None) -> tuple[str, list[dict]]:
    """Retrieve relevant maintenance context from the local ChromaDB store."""
    if not query.strip():
        return "", []

    ordered_priority = priority_sources or []

    try:
        embed_response = requests.post(
            EMBED_URL,
            json={"model": EMBED_MODEL, "prompt": query},
            timeout=60,
        )
        if embed_response.status_code != 200:
            return "", []

        embedding = embed_response.json().get("embedding")
        if not embedding:
            return "", []

        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection = client.get_collection(name=RAG_COLLECTION)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        sources = []
        for meta in metadatas:
            if not isinstance(meta, dict):
                continue
            source = meta.get("source")
            category = meta.get("category", "Reference")
            if source and not any(
                item.get("source") == source and item.get("category") == category
                for item in sources
            ):
                sources.append({"source": source, "category": category})

        if ordered_priority:
            indexed_priority = {name: index for index, name in enumerate(ordered_priority)}
            sources.sort(
                key=lambda item: (
                    indexed_priority.get(item["source"], len(ordered_priority)),
                    item["source"],
                )
            )

        return "\n\n".join(documents), sources
    except (requests.RequestException, ValueError, KeyError):
        return "", []
    except Exception:
        return "", []


@app.on_event("startup")
def on_startup() -> None:
    """Initialize local SQLite database on app startup."""
    init_db()


def get_health_status() -> dict:
    """Return basic health status for API, database, and Ollama."""
    database_status = "ok"
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("SELECT 1")
    except sqlite3.Error:
        database_status = "unreachable"

    ollama_status = "ok"
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            ollama_status = "unreachable"
    except requests.RequestException:
        ollama_status = "unreachable"

    return {
        "api": "ok",
        "ollama": ollama_status,
        "database": database_status,
    }


class PredictionInput(BaseModel):
    """Input schema for one machine record."""

    Type: Literal["L", "M", "H"]
    Air_temperature_K: float
    Process_temperature_K: float
    Rotational_speed_rpm: float
    Torque_Nm: float
    Tool_wear_min: float


def generate_llm_explanation(
    prediction: int,
    rag_context: str,
    thermal_status: str,
    wear_status: str,
    torque_status: str,
    overall_risk_status: str,
    recommended_actions: list[str],
) -> str:
    """Generate a short explanation using a local Ollama Gemma model."""

    risk_text = (
        "The ML system predicted elevated failure risk."
        if prediction == 1
        else "The ML system predicted low failure risk."
    )

    context_block = rag_context.strip() or "No relevant maintenance context available."

    prompt = f"""
You are an industrial maintenance assistant.
Use the provided maintenance context when relevant. Do not invent faults.

Maintenance context:
{context_block}

Validated System Status:
- Thermal Status: {thermal_status}
- Wear Status: {wear_status}
- Torque Status: {torque_status}
- Overall Risk Status: {overall_risk_status}

Validated Severity Ceiling:
- normal: no urgent language
- preventive: monitor or scheduled inspection only
- alert: inspection recommended
- urgent: immediate inspection

Recommended Actions:
{', '.join(recommended_actions) if recommended_actions else 'None'}

{risk_text}

Write a short explanation in practical engineering language.
Explain the validated system statuses and recommended actions only.
Do not reinterpret numeric thresholds or infer extra conditions.
Do not mention raw sensor values or temperature differences.
Do not invent unrelated concerns.
Do not escalate beyond validated system state.
If the validated state is preventive, never use "immediate", "urgent", "prioritize before operation", "critical", or "shutdown".
If the condition alert is "Preventive Wear Advisory", use only preventive-tier language.
Preventive-tier allowed phrases: "monitor", "review", "scheduled maintenance", "routine inspection", "next maintenance cycle".
Preventive-tier blocked phrases: "thorough inspection", "immediate inspection", "urgent inspection", "diagnostic inspection".
Recommended actions must align with the provided actions list and the explanation must not exceed their severity.
If "Monitor wear trend" is in the actions list, make it the primary recommendation.
Do not mention probability unless necessary.
Do not invent faults.
Use only the provided statuses and recommended actions.
Keep the answer under 3 sentences.
"""

    # Handle local LLM connection issues gracefully when Ollama is not running.
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",
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


@app.get("/health")
def read_health() -> dict:
    """Return health status for local dependencies."""
    return get_health_status()


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
    temp_diff = abs(payload.Process_temperature_K - payload.Air_temperature_K)
    high_torque = payload.Torque_Nm > 60
    high_tool_wear = payload.Tool_wear_min > 150
    if temp_diff < 10:
        thermal_status = "Normal"
    elif temp_diff <= 20:
        thermal_status = "Warning"
    else:
        thermal_status = "High"

    if payload.Tool_wear_min < 120:
        wear_status = "Normal"
    elif payload.Tool_wear_min <= 150:
        wear_status = "Preventive"
    else:
        wear_status = "Alert"

    torque_status = "High" if high_torque else "Normal"
    if payload.Tool_wear_min < 120:
        tool_wear_tier = "Normal"
    elif payload.Tool_wear_min <= 150:
        tool_wear_tier = "Preventive Wear Advisory"
    elif payload.Tool_wear_min <= 180:
        tool_wear_tier = "Maintenance Alert"
    else:
        tool_wear_tier = "Urgent Wear Alert"
    rag_terms = []
    if high_torque:
        rag_terms.append("high torque mechanical load friction misalignment lubrication")
    if high_tool_wear:
        rag_terms.append("high tool wear inspection tool replacement maintenance")
    if temp_diff > 10:
        rag_terms.append("large temperature difference cooling inefficiency abnormal heat")
    if prediction == 1:
        rag_terms.append("failure risk maintenance SOP safety guideline")

    rag_query = " ".join(rag_terms).strip()
    if not rag_query:
        rag_query = "normal operating conditions preventive maintenance"

    priority_sources = []
    if temp_diff > 10:
        priority_sources.extend(["machine_manual.txt", "safety_guidelines.txt"])
    if high_tool_wear:
        priority_sources.extend(["maintenance_sop.txt", "failure_cases.txt"])
    if high_torque:
        priority_sources.extend(["machine_manual.txt", "maintenance_sop.txt"])
    if priority_sources:
        priority_sources = list(dict.fromkeys(priority_sources))

    rag_context, rag_sources = get_rag_context(rag_query, priority_sources)

    trend_alerts = []
    recent_history = get_recent_history(3)
    if len(recent_history) >= 2:
        prev = recent_history[0]
        prev2 = recent_history[1]
        prev_temp_diff = abs(prev["process_temperature_k"] - prev["air_temperature_k"])
        prev2_temp_diff = abs(prev2["process_temperature_k"] - prev2["air_temperature_k"])

        if temp_diff > prev_temp_diff and prev_temp_diff > prev2_temp_diff:
            trend_alerts.append("Rising Thermal Trend")

        if payload.Torque_Nm > prev["torque_nm"] and prev["torque_nm"] > prev2["torque_nm"]:
            trend_alerts.append("Increasing Load Trend")

        delta_now = payload.Tool_wear_min - prev["tool_wear_min"]
        delta_prev = prev["tool_wear_min"] - prev2["tool_wear_min"]
        if delta_now > 0 and delta_now > delta_prev:
            trend_alerts.append("Accelerated Tool Wear")

    alerts = []
    actions = []
    if temp_diff > 10:
        if temp_diff <= 20:
            thermal_label = "Thermal Warning"
            thermal_severity = "warning"
        elif temp_diff <= 40:
            thermal_label = "Thermal Alert"
            thermal_severity = "alert"
        else:
            thermal_label = "Critical Thermal Alert"
            thermal_severity = "critical"
        alerts.append({"label": thermal_label, "severity": thermal_severity})
        if thermal_label == "Thermal Warning":
            actions.extend(
                [
                    "Check cooling efficiency",
                    "Monitor temperature trend",
                    "Review process load",
                ]
            )
    if high_torque:
        alerts.append({"label": "Torque Load Alert", "severity": "alert"})
        actions.extend(["Check load conditions", "Inspect lubrication"])
    if tool_wear_tier == "Preventive Wear Advisory":
        alerts.append({"label": "Preventive Wear Advisory", "severity": "warning"})
        actions.append("Monitor wear trend")
    elif tool_wear_tier == "Maintenance Alert":
        alerts.append({"label": "Maintenance Alert", "severity": "alert"})
        actions.append("Inspect tool condition")
    elif tool_wear_tier == "Urgent Wear Alert":
        alerts.append({"label": "Urgent Wear Alert", "severity": "critical"})
        actions.append("Immediate inspection")

    if prediction == 1:
        overall_risk_status = "High"
    elif any(alerts):
        overall_risk_status = "Caution"
    else:
        overall_risk_status = "Normal"

    explanation = generate_llm_explanation(
        prediction,
        rag_context,
        thermal_status,
        wear_status,
        torque_status,
        overall_risk_status,
        actions,
    )

    # Save prediction input/output to local SQLite history.
    save_prediction_history(payload, prediction, failure_probability, explanation)

    return {
        "prediction": prediction,
        "failure_probability": failure_probability,
        "explanation": explanation,
        "rag_sources": rag_sources,
        "alerts": alerts,
        "recommended_actions": actions,
        "trend_alerts": trend_alerts,
    }
