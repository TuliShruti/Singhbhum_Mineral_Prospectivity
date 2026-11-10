
import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# 1. Load integrated dataset
df = pd.read_csv("data/processed/integrated_geophysical.csv")

# 2. Select ML features
features = [
    "bouguer_anomaly",
    "magnetic_anomaly_nt",
    "elevation"
]

X = df[features].copy()

# 3. Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Train Isolation Forest
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

model.fit(X_scaled)

# 5. Predict anomalies
# 1 = Normal, -1 = Anomaly
df["anomaly_label"] = model.predict(X_scaled)

# 6. Calculate anomaly scores
df["anomaly_score"] = model.decision_function(X_scaled)

# Lower decision_function values indicate more unusual observations.
# Sort so the most anomalous observations appear first.
df = df.sort_values("anomaly_score", ascending=True)

# 7. Save results
df.to_csv(
    "data/outputs/isolation_forest_results.csv",
    index=False
)

# 8. Print summary
print("\nISOLATION FOREST RESULTS")

print("Total observations:", len(df))

print(
    "Normal observations:",
    (df["anomaly_label"] == 1).sum()
)

print(
    "Anomalous observations:",
    (df["anomaly_label"] == -1).sum()
)

print("\nTOP 15 ANOMALOUS LOCATIONS")

print(
    df[[
        "longitude",
        "latitude",
        "bouguer_anomaly",
        "magnetic_anomaly_nt",
        "elevation",
        "anomaly_score",
        "anomaly_label"
    ]].head(15).to_string(index=False)
)

print("\nResults saved successfully.")
