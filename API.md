# API Documentation

## Overview

The FastAPI backend provides REST endpoints for machine learning predictions and history management. All endpoints expect JSON requests and return JSON responses.

**Base URL:** `http://127.0.0.1:8000`

## Authentication

Currently, no authentication is required. This is an MVP - authentication should be added before production deployment.

## Endpoints

### 1. Health Check

**GET** `/`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200 OK` - API is running

---

### 2. Make Prediction

**POST** `/predict`

Submit sensor readings and receive a failure risk prediction with LLM explanation.

**Request Body:**
```json
{
  "Type": "M",
  "Air_temperature_K": 305.5,
  "Process_temperature_K": 315.2,
  "Rotational_speed_rpm": 1500,
  "Torque_Nm": 40.5,
  "Tool_wear_min": 25
}
```

**Request Fields:**
| Field | Type | Description | Range |
|-------|------|-------------|-------|
| Type | string | Machine type | M, L, H |
| Air_temperature_K | number | Air temperature in Kelvin | ~300-330 |
| Process_temperature_K | number | Process temperature in Kelvin | ~305-340 |
| Rotational_speed_rpm | number | Rotation speed in RPM | 1000-3000 |
| Torque_Nm | number | Torque in Newton-meters | 0-100 |
| Tool_wear_min | number | Tool wear in minutes | 0-250 |

**Response:**
```json
{
  "prediction": 0,
  "failure_probability": 0.15,
  "explanation": "The current operating parameters indicate normal conditions with no anomalies detected..."
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| prediction | integer | 0 = No failure, 1 = Failure |
| failure_probability | number | Probability of failure (0-1) |
| explanation | string | Natural language explanation from Gemma LLM |

**Status Codes:**
- `200 OK` - Prediction successful
- `422 Unprocessable Entity` - Invalid request format

**Example with cURL:**
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "M",
    "Air_temperature_K": 305.5,
    "Process_temperature_K": 315.2,
    "Rotational_speed_rpm": 1500,
    "Torque_Nm": 40.5,
    "Tool_wear_min": 25
  }'
```

---

### 3. Get Prediction History

**GET** `/history`

Retrieve the latest predictions stored in the database.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| limit | integer | Maximum records to return | 20 |

**Response:**
```json
[
  {
    "id": 1,
    "created_at": "2026-04-30T11:05:26.081848",
    "machine_type": "M",
    "air_temperature_k": 305.5,
    "process_temperature_k": 315.2,
    "rotational_speed_rpm": 1500,
    "torque_nm": 40.5,
    "tool_wear_min": 25,
    "prediction": 0,
    "failure_probability": 0.15,
    "explanation": "The current operating parameters indicate normal conditions..."
  }
]
```

**Status Codes:**
- `200 OK` - Records retrieved successfully
- `204 No Content` - No records found

---

### 4. Clear History

**DELETE** `/history`

Delete all predictions from the database.

**Response:**
```json
{
  "message": "History cleared"
}
```

**Status Codes:**
- `200 OK` - History cleared successfully

---

## Error Handling

All errors return a JSON response with error details:

```json
{
  "detail": "Error description"
}
```

**Common Errors:**

| Status | Message | Cause |
|--------|---------|-------|
| 422 | Validation error | Invalid request format or missing fields |
| 500 | Internal server error | Backend processing error |

---

## Integration Examples

### Python

```python
import requests

# Make a prediction
url = "http://127.0.0.1:8000/predict"
payload = {
    "Type": "M",
    "Air_temperature_K": 305,
    "Process_temperature_K": 315,
    "Rotational_speed_rpm": 1500,
    "Torque_Nm": 40,
    "Tool_wear_min": 25
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Failure Probability: {result['failure_probability']*100:.1f}%")
print(f"Explanation: {result['explanation']}")
```

### JavaScript

```javascript
// Make a prediction
const payload = {
  Type: "M",
  Air_temperature_K: 305,
  Process_temperature_K: 315,
  Rotational_speed_rpm: 1500,
  Torque_Nm: 40,
  Tool_wear_min: 25
};

fetch("http://127.0.0.1:8000/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
  .then(r => r.json())
  .then(data => {
    console.log(`Failure Probability: ${(data.failure_probability*100).toFixed(1)}%`);
    console.log(`Explanation: ${data.explanation}`);
  });
```

---

## Rate Limiting

Currently not implemented. Should be added before production use.

## CORS

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

---

## Database

Predictions are persisted in SQLite database (`predictions.db`). The history endpoint returns the 20 most recent predictions by default.

---

## Notes for Developers

- Ollama LLM service must be running at `localhost:11434`
- LLM explanations have a 180-second timeout
- Model artifacts are loaded from `models/` directory on startup
- CORS is configured for local development only

---

For more information, see the main [README.md](README.md).
