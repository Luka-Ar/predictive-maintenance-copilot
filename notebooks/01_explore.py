"""Initial dataset exploration for Predictive Maintenance Copilot.

This script focuses only on understanding the data.
No modeling is done here.
"""

from pathlib import Path
import sys

import pandas as pd

# Build a path that always points to: project_root/data/ai4i2020.csv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "ai4i2020.csv"

# Stop early with a clear message if the dataset is missing.
if not DATA_PATH.exists():
    print(f"Dataset not found at: {DATA_PATH}")
    print("Please place 'ai4i2020.csv' inside the data/ folder and run again.")
    sys.exit(1)

# Load the dataset into a pandas DataFrame.
df = pd.read_csv(DATA_PATH)

# 1) Show the first 5 rows to quickly inspect the data.
print("\n=== First 5 Rows ===")
print(df.head())

# 2) Show all column names.
print("\n=== Column Names ===")
print(df.columns.tolist())

# 3) Show DataFrame info (rows, columns, data types, non-null counts).
print("\n=== DataFrame Info ===")
df.info()

# 4) Show missing values per column.
print("\n=== Missing Values Per Column ===")
print(df.isnull().sum())

# 5) Show value counts for Machine failure (if the column exists).
print("\n=== Value Counts: Machine failure ===")
if "Machine failure" in df.columns:
    print(df["Machine failure"].value_counts(dropna=False))
else:
    print("Column 'Machine failure' was not found in the dataset.")

# 6) Print all columns related to failure types if they exist.
# We check both name pattern matches and common AI4I failure-type columns.
known_failure_type_columns = ["TWF", "HDF", "PWF", "OSF", "RNF"]
pattern_failure_columns = [
    col for col in df.columns if "failure" in col.lower() and col != "Machine failure"
]
existing_known_failure_columns = [col for col in known_failure_type_columns if col in df.columns]

failure_type_columns = sorted(set(pattern_failure_columns + existing_known_failure_columns))

print("\n=== Failure-Type Columns (if any) ===")
if failure_type_columns:
    print(failure_type_columns)
    print("\nValue counts for each failure-type column:")
    for col in failure_type_columns:
        print(f"\n- {col}")
        print(df[col].value_counts(dropna=False))
else:
    print("No failure-type columns were found.")
