from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "data" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(PROC / "integrated_geophysical.csv")
features = [
    "magnetic_anomaly_nt_mean",
    "bouguer_anomaly_mean",
    "elevation_mean",
]
X = df[features].replace([np.inf, -np.inf], np.nan)
imputer = SimpleImputer(strategy="median")
X_imp = imputer.fit_transform(X)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imp)

# Exploratory outlier screening only; contamination is a user-chosen screening fraction.
model = IsolationForest(
    n_estimators=300,
    contamination=0.05,
    random_state=42,
)
model.fit(X_scaled)

result = df.copy()
result["isolation_forest_label"] = model.predict(X_scaled)  # -1 = outlier, +1 = inlier
result["anomaly_score"] = -model.decision_function(X_scaled)  # larger = more unusual
result["anomaly_rank_percentile"] = result["anomaly_score"].rank(pct=True)

pca = PCA(n_components=2, random_state=42)
pcs = pca.fit_transform(X_scaled)
result["PC1"] = pcs[:, 0]
result["PC2"] = pcs[:, 1]

result.to_csv(OUT / "isolation_forest_anomaly_scores.csv", index=False)

pca_info = pd.DataFrame({
    "component": ["PC1", "PC2"],
    "explained_variance_ratio": pca.explained_variance_ratio_,
})
pca_info.to_csv(OUT / "pca_explained_variance.csv", index=False)

print("Isolation Forest complete.")
print("Feature columns:", features)
print("Number of stations:", len(result))
print("Flagged outliers:", int((result.isolation_forest_label == -1).sum()))
print("PCA explained variance:", pca.explained_variance_ratio_)
print(result.sort_values("anomaly_score", ascending=False)[
    ["longitude", "latitude", *features, "anomaly_score", "isolation_forest_label"]
].head(10).to_string(index=False))
