
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import Transformer
from scipy.spatial import cKDTree

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

purbi_file = Path(
    "data/outputs/copper_occurrence_nearest_station_distances.csv"
)

galudih_file = Path(
    "data/outputs/copper_73F09_nearest_station_distances.csv"
)

anomaly_file = Path(
    "data/outputs/isolation_forest_results.csv"
)

output_dir = Path("data/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# Check whether input files exist
for file in [purbi_file, galudih_file, anomaly_file]:
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file}")

# --------------------------------------------------
# 2. LOAD COPPER OCCURRENCES
# --------------------------------------------------

purbi = pd.read_csv(purbi_file)
galudih = pd.read_csv(galudih_file)

purbi["source_dataset"] = "Purbi Singhbhum"
galudih["source_dataset"] = "Galudih 73F09"

copper = pd.concat(
    [purbi, galudih],
    ignore_index=True
)

# Required columns
required = ["longitude", "latitude"]

for col in required:
    if col not in copper.columns:
        raise ValueError(f"Missing column: {col}")

copper["longitude"] = pd.to_numeric(
    copper["longitude"], errors="coerce"
)

copper["latitude"] = pd.to_numeric(
    copper["latitude"], errors="coerce"
)

copper = copper.dropna(
    subset=["longitude", "latitude"]
).copy()

# --------------------------------------------------
# 3. LOAD ISOLATION FOREST RESULTS
# --------------------------------------------------

df = pd.read_csv(anomaly_file)

anomalies = df[
    df["anomaly_label"] == -1
].copy()

print("Total copper occurrences:", len(copper))
print("Flagged anomaly records:", len(anomalies))

# --------------------------------------------------
# 4. HANDLE NEAR-DUPLICATE ANOMALY COORDINATES
# --------------------------------------------------

# Round coordinates to 4 decimal places.
# This groups locations within approximately 10-11 metres
# in this study area. It is a reporting convention,
# not proof that the original records are duplicates.

anomalies["lon_group"] = anomalies["longitude"].round(4)
anomalies["lat_group"] = anomalies["latitude"].round(4)

anomaly_sites = (
    anomalies.groupby(["lon_group", "lat_group"])
    .agg(
        longitude=("longitude", "mean"),
        latitude=("latitude", "mean"),
        anomaly_score=("anomaly_score", "min"),
        record_count=("anomaly_label", "size")
    )
    .reset_index(drop=True)
)

print("Approximate distinct anomaly sites:", len(anomaly_sites))

# --------------------------------------------------
# 5. CONVERT COORDINATES TO UTM ZONE 45N
# --------------------------------------------------

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True
)

# Copper coordinates
copper_x, copper_y = transformer.transform(
    copper["longitude"].to_numpy(),
    copper["latitude"].to_numpy()
)

copper_coords = np.column_stack(
    (copper_x, copper_y)
)

# Anomaly coordinates
anomaly_x, anomaly_y = transformer.transform(
    anomaly_sites["longitude"].to_numpy(),
    anomaly_sites["latitude"].to_numpy()
)

anomaly_coords = np.column_stack(
    (anomaly_x, anomaly_y)
)

# --------------------------------------------------
# 6. FIND NEAREST ML ANOMALY
# --------------------------------------------------

tree = cKDTree(anomaly_coords)

distances, indices = tree.query(copper_coords, k=1)

# Distances are in metres; convert to kilometres
copper["nearest_ml_anomaly_km"] = distances / 1000

# Store nearest anomaly coordinates
copper["nearest_anomaly_longitude"] = (
    anomaly_sites.iloc[indices]["longitude"].to_numpy()
)

copper["nearest_anomaly_latitude"] = (
    anomaly_sites.iloc[indices]["latitude"].to_numpy()
)

copper["nearest_anomaly_score"] = (
    anomaly_sites.iloc[indices]["anomaly_score"].to_numpy()
)

# --------------------------------------------------
# 7. DISTANCE CATEGORY FLAGS
# --------------------------------------------------

for threshold in [1, 5, 10, 20]:
    copper[f"within_{threshold}km_ml_anomaly"] = (
        copper["nearest_ml_anomaly_km"] <= threshold
    )

# --------------------------------------------------
# 8. SAVE DETAILED RESULTS
# --------------------------------------------------

columns_to_save = [
    "source_dataset",
    "locality",
    "toposheet",
    "commodity",
    "longitude",
    "latitude",
    "nearest_gravity_distance_km",
    "nearest_magnetic_distance_km",
    "nearest_ml_anomaly_km",
    "nearest_anomaly_longitude",
    "nearest_anomaly_latitude",
    "nearest_anomaly_score",
    "within_1km_ml_anomaly",
    "within_5km_ml_anomaly",
    "within_10km_ml_anomaly",
    "within_20km_ml_anomaly"
]

# Keep only columns that exist in the input files
columns_to_save = [
    col for col in columns_to_save if col in copper.columns
]

result = copper[columns_to_save].copy()

result.to_csv(
    output_dir / "copper_to_nearest_ml_anomaly.csv",
    index=False
)

# --------------------------------------------------
# 9. SUMMARY
# --------------------------------------------------

print("\nCOPPER OCCURRENCE - ML ANOMALY VALIDATION")

print(
    result[
        [
            "source_dataset",
            "locality",
            "nearest_ml_anomaly_km"
        ]
    ].to_string(index=False)
)

print("\nDISTANCE SUMMARY (KM)")

print(
    result.groupby("source_dataset")[
        "nearest_ml_anomaly_km"
    ].describe()
)

print("\nOCCURRENCES WITHIN ANOMALY DISTANCE THRESHOLDS")

for threshold in [1, 5, 10, 20]:
    col = f"within_{threshold}km_ml_anomaly"

    print(
        f"Within {threshold} km:",
        int(result[col].sum()),
        "out of",
        len(result)
    )

print("\nOUTPUT SAVED:")
print(output_dir / "copper_to_nearest_ml_anomaly.csv")
