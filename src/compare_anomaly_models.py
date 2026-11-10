
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

df = pd.read_csv(
    "data/processed/integrated_geophysical.csv"
)

features = [
    "bouguer_anomaly",
    "magnetic_anomaly_nt",
    "elevation"
]

X = df[features].copy()

# --------------------------------------------------
# 2. SCALE FEATURES
# --------------------------------------------------

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --------------------------------------------------
# 3. ISOLATION FOREST
# --------------------------------------------------

iso = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

iso_labels = iso.fit_predict(X_scaled)

# --------------------------------------------------
# 4. LOCAL OUTLIER FACTOR
# --------------------------------------------------

lof = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.05
)

lof_labels = lof.fit_predict(X_scaled)

# --------------------------------------------------
# 5. ONE-CLASS SVM
# --------------------------------------------------

svm = OneClassSVM(
    kernel="rbf",
    gamma="scale",
    nu=0.05
)

svm_labels = svm.fit_predict(X_scaled)

# --------------------------------------------------
# 6. STORE RESULTS
# --------------------------------------------------

results = df.copy()

# sklearn convention:
# 1 = Normal
# -1 = Anomaly

results["isolation_forest"] = iso_labels
results["lof"] = lof_labels
results["one_class_svm"] = svm_labels

# Count how many models flag each observation
results["models_flagged"] = (
    (results["isolation_forest"] == -1).astype(int)
    + (results["lof"] == -1).astype(int)
    + (results["one_class_svm"] == -1).astype(int)
)

# --------------------------------------------------
# 7. MODEL SUMMARY
# --------------------------------------------------

models = {
    "Isolation Forest": iso_labels,
    "Local Outlier Factor": lof_labels,
    "One-Class SVM": svm_labels
}

print("\nMODEL COMPARISON")

for name, labels in models.items():

    count = np.sum(labels == -1)

    print(f"\n{name}")
    print("Anomalies:", count)
    print("Normal:", np.sum(labels == 1))
    print(
        "Anomaly percentage:",
        round(count / len(labels) * 100, 2),
        "%"
    )

# --------------------------------------------------
# 8. AGREEMENT BETWEEN MODELS
# --------------------------------------------------

print("\nMODEL AGREEMENT")

for i, (name1, labels1) in enumerate(models.items()):

    for name2, labels2 in list(models.items())[i+1:]:

        common = np.sum(
            (labels1 == -1) & (labels2 == -1)
        )

        print(
            f"{name1} and {name2}:",
            common,
            "common anomalous observations"
        )

# --------------------------------------------------
# 9. CONSENSUS ANOMALIES
# --------------------------------------------------

consensus = results[
    results["models_flagged"] >= 2
].copy()

print("\nCONSENSUS RESULTS")
print("Observations flagged by at least 2 models:",
      len(consensus))

# --------------------------------------------------
# 10. SAVE RESULTS
# --------------------------------------------------

results.to_csv(
    "data/outputs/model_comparison_results.csv",
    index=False
)

consensus.to_csv(
    "data/outputs/consensus_anomalies.csv",
    index=False
)

print("\nFiles saved successfully.")
