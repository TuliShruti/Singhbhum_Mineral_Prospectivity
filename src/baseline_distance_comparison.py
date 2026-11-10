
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import Transformer
from scipy.spatial import cKDTree

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

copper_file = Path(
    "data/outputs/copper_occurrence_nearest_station_distances.csv"
)

anomaly_file = Path(
    "data/outputs/isolation_forest_results.csv"
)

output_dir = Path("data/outputs")
output_dir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

copper = pd.read_csv(copper_file)
df = pd.read_csv(anomaly_file)

# Primary comparison: 14 Purbi Singhbhum occurrences
# Galudih is excluded because it is outside effective
# geophysical station coverage.

required_copper = ["locality", "longitude", "latitude"]
required_model = [
    "longitude", "latitude", "anomaly_label"
]

for col in required_copper:
    if col not in copper.columns:
        raise ValueError(f"Missing copper column: {col}")

for col in required_model:
    if col not in df.columns:
        raise ValueError(f"Missing model column: {col}")

copper = copper.dropna(
    subset=["longitude", "latitude"]
).copy()

df = df.dropna(
    subset=["longitude", "latitude", "anomaly_label"]
).copy()

# --------------------------------------------------
# 3. SEPARATE ANOMALOUS AND NORMAL OBSERVATIONS
# --------------------------------------------------

anomalies = df[df["anomaly_label"] == -1].copy()
normal = df[df["anomaly_label"] == 1].copy()

print("Copper occurrences:", len(copper))
print("Anomaly records:", len(anomalies))
print("Normal records:", len(normal))

# --------------------------------------------------
# 4. GROUP NEAR-DUPLICATE COORDINATES
# --------------------------------------------------

# Use the same coordinate grouping for both categories.
# Rounding to 4 decimal places corresponds to roughly
# 10-11 metres in this study area.

def get_unique_locations(data):

    temp = data.copy()

    temp["lon_group"] = temp["longitude"].round(4)
    temp["lat_group"] = temp["latitude"].round(4)

    return (
        temp.groupby(["lon_group", "lat_group"])
        .agg(
            longitude=("longitude", "mean"),
            latitude=("latitude", "mean")
        )
        .reset_index(drop=True)
    )


anomaly_sites = get_unique_locations(anomalies)
normal_sites = get_unique_locations(normal)
all_sites = get_unique_locations(df)

print("\nUNIQUE LOCATION COUNTS")
print("Anomaly sites:", len(anomaly_sites))
print("Normal sites:", len(normal_sites))
print("All observation sites:", len(all_sites))

# --------------------------------------------------
# 5. CONVERT COORDINATES TO UTM ZONE 45N
# --------------------------------------------------

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True
)


def project_coordinates(data):

    x, y = transformer.transform(
        data["longitude"].to_numpy(),
        data["latitude"].to_numpy()
    )

    return np.column_stack((x, y))


copper_coords = project_coordinates(copper)
anomaly_coords = project_coordinates(anomaly_sites)
normal_coords = project_coordinates(normal_sites)
all_coords = project_coordinates(all_sites)

# --------------------------------------------------
# 6. BUILD NEAREST-NEIGHBOUR TREES
# --------------------------------------------------

anomaly_tree = cKDTree(anomaly_coords)
normal_tree = cKDTree(normal_coords)
all_tree = cKDTree(all_coords)

# --------------------------------------------------
# 7. CALCULATE DISTANCES
# --------------------------------------------------

# Distances returned by cKDTree are in metres.

distance_anomaly, anomaly_idx = anomaly_tree.query(
    copper_coords, k=1
)

distance_normal, normal_idx = normal_tree.query(
    copper_coords, k=1
)

distance_station, station_idx = all_tree.query(
    copper_coords, k=1
)

# Convert metres to kilometres.

copper["nearest_anomaly_km"] = distance_anomaly / 1000

copper["nearest_normal_km"] = distance_normal / 1000

copper["nearest_any_station_km"] = distance_station / 1000

# --------------------------------------------------
# 8. IDENTIFY NEAREST LOCATIONS
# --------------------------------------------------

copper["nearest_anomaly_longitude"] = (
    anomaly_sites.iloc[anomaly_idx]["longitude"].to_numpy()
)

copper["nearest_anomaly_latitude"] = (
    anomaly_sites.iloc[anomaly_idx]["latitude"].to_numpy()
)

copper["nearest_normal_longitude"] = (
    normal_sites.iloc[normal_idx]["longitude"].to_numpy()
)

copper["nearest_normal_latitude"] = (
    normal_sites.iloc[normal_idx]["latitude"].to_numpy()
)

# --------------------------------------------------
# 9. COMPARE ANOMALY AND NORMAL DISTANCES
# --------------------------------------------------

copper["distance_difference_km"] = (
    copper["nearest_normal_km"]
    - copper["nearest_anomaly_km"]
)

copper["closer_to_anomaly"] = (
    copper["distance_difference_km"] > 0
)

copper["distance_ratio"] = (
    copper["nearest_anomaly_km"]
    / copper["nearest_normal_km"].replace(0, np.nan)
)

# --------------------------------------------------
# 10. SAVE DETAILED RESULTS
# --------------------------------------------------

result_columns = [
    "locality",
    "longitude",
    "latitude",
    "nearest_anomaly_km",
    "nearest_normal_km",
    "nearest_any_station_km",
    "distance_difference_km",
    "distance_ratio",
    "closer_to_anomaly",
    "nearest_anomaly_longitude",
    "nearest_anomaly_latitude",
    "nearest_normal_longitude",
    "nearest_normal_latitude"
]

result = copper[result_columns].copy()

result.to_csv(
    output_dir / "baseline_distance_comparison.csv",
    index=False
)

# --------------------------------------------------
# 11. SUMMARY STATISTICS
# --------------------------------------------------

print("\nBASELINE DISTANCE COMPARISON")

print(
    result[
        [
            "locality",
            "nearest_anomaly_km",
            "nearest_normal_km",
            "nearest_any_station_km",
            "distance_difference_km",
            "closer_to_anomaly"
        ]
    ].to_string(index=False)
)

print("\nDISTANCE STATISTICS (KM)")

print(
    result[
        [
            "nearest_anomaly_km",
            "nearest_normal_km",
            "nearest_any_station_km"
        ]
    ].describe().round(3)
)

print("\nCOMPARISON SUMMARY")

print(
    "Occurrences closer to an anomaly:",
    int(result["closer_to_anomaly"].sum())
)

print(
    "Occurrences closer to a normal observation:",
    int((~result["closer_to_anomaly"]).sum())
)

print(
    "Mean anomaly distance:",
    round(result["nearest_anomaly_km"].mean(), 3), "km"
)

print(
    "Mean normal distance:",
    round(result["nearest_normal_km"].mean(), 3), "km"
)

print(
    "Mean distance difference:",
    round(result["distance_difference_km"].mean(), 3), "km"
)

# --------------------------------------------------
# 12. SAVE SUMMARY CSV
# --------------------------------------------------

summary = pd.DataFrame({
    "metric": [
        "Number of copper occurrences",
        "Mean nearest anomaly distance (km)",
        "Mean nearest normal distance (km)",
        "Mean nearest station distance (km)",
        "Median nearest anomaly distance (km)",
        "Median nearest normal distance (km)",
        "Occurrences closer to anomaly",
        "Occurrences closer to normal observation"
    ],
    "value": [
        len(result),
        result["nearest_anomaly_km"].mean(),
        result["nearest_normal_km"].mean(),
        result["nearest_any_station_km"].mean(),
        result["nearest_anomaly_km"].median(),
        result["nearest_normal_km"].median(),
        result["closer_to_anomaly"].sum(),
        (~result["closer_to_anomaly"]).sum()
    ]
})

summary.to_csv(
    output_dir / "baseline_distance_summary.csv",
    index=False
)

print("\nOUTPUT FILES CREATED:")
print("1. data/outputs/baseline_distance_comparison.csv")
print("2. data/outputs/baseline_distance_summary.csv")
