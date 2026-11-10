
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data/processed/integrated_geophysical.csv")

# Separate strong positive and negative magnetic observations
positive = df[df["magnetic_anomaly_nt"] > 500].copy()
negative = df[df["magnetic_anomaly_nt"] < -500].copy()

print("Strong positive anomalies:", len(positive))
print("Strong negative anomalies:", len(negative))

# Display their coordinates
print("\nPOSITIVE ANOMALIES")
print(positive[
    ["longitude", "latitude", "magnetic_anomaly_nt"]
].sort_values("magnetic_anomaly_nt", ascending=False).to_string(index=False))

print("\nNEGATIVE ANOMALIES")
print(negative[
    ["longitude", "latitude", "magnetic_anomaly_nt"]
].sort_values("magnetic_anomaly_nt").to_string(index=False))

# Cluster geographical coordinates.
# Convert longitude/latitude approximately to kilometres.
# Study area is around 22.4 degrees latitude.
coords = df[["longitude", "latitude"]].to_numpy()

coords_km = coords.copy()
coords_km[:, 0] *= 111.32 * np.cos(np.radians(22.4))
coords_km[:, 1] *= 111.32

# DBSCAN groups nearby observation locations.
dbscan = DBSCAN(eps=3, min_samples=3)
df["spatial_cluster"] = dbscan.fit_predict(coords_km)

print("\nSPATIAL CLUSTER COUNTS")
print(df["spatial_cluster"].value_counts().sort_index())

# Show cluster-wise magnetic anomaly statistics
print("\nCLUSTER MAGNETIC STATISTICS")
print(
    df.groupby("spatial_cluster")["magnetic_anomaly_nt"]
      .agg(["count", "mean", "std", "min", "max"])
)
