"""Train a baseline model for machine failure prediction.

This script:
1) Loads the AI4I dataset
2) Prepares features and target
3) Trains a RandomForest baseline model
4) Evaluates results
5) Saves the model and feature columns
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Build project paths (works even when script is run from different locations).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "ai4i2020.csv"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "failure_model.joblib"
FEATURE_COLUMNS_PATH = MODELS_DIR / "feature_columns.joblib"

# Load dataset.
df = pd.read_csv(DATA_PATH)

# Drop IDs and failure-type flag columns to avoid leaking direct failure labels.
df = df.drop(
    columns=["UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"],
    errors="ignore",
)

# Set target column.
target_col = "Machine failure"

# Separate features (X) and target (y).
X = df.drop(columns=[target_col])
y = df[target_col]

# Convert categorical column "Type" using one-hot encoding.
X = pd.get_dummies(X, columns=["Type"], drop_first=False)

# Split data into train/test with stratification.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# Create and train a baseline RandomForest model.
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
)
model.fit(X_train, y_train)

# Use probability-based predictions so we can tune the failure detection threshold.
# A lower threshold can improve recall for rare failure events.
threshold = 0.3
failure_probabilities = model.predict_proba(X_test)[:, 1]
y_pred = (failure_probabilities >= threshold).astype(int)

# Print evaluation results clearly.
print("\n" + "=" * 50)
print("Baseline Model Evaluation")
print("=" * 50)
print(f"Using threshold = {threshold}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Save outputs.
MODELS_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)
joblib.dump(X.columns.tolist(), FEATURE_COLUMNS_PATH)

print("\n" + "=" * 50)
print("Saved Artifacts")
print("=" * 50)
print(f"Model saved to: {MODEL_PATH}")
print(f"Feature columns saved to: {FEATURE_COLUMNS_PATH}")
