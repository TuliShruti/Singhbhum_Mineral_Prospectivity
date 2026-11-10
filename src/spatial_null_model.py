
import pandas as pd
import numpy as np

from pyproj import Transformer
from scipy.spatial import cKDTree

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

copper = pd.read_csv(
    "data/outputs/copper_occurrence_nearest_station_distances.csv"
)

df = pd.read_csv(
    "data/outputs/isolation_forest_results.csv"
)

# Remove missing coordinates
copper = copper.dropna(
    subset=["longitude", "latitude"]
).copy()

df = df.dropna(
    subset=["longitude", "latitude", "anomaly_label"]
).copy()

# --------------------------------------------------
# 2. SEPARATE ANOMALY AND NORMAL LOCATIONS
# --------------------------------------------------

def unique_locations(data):

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


anomalies = unique_locations(
    df[df["anomaly_label"] == -1]
)

normal = unique_locations(
    df[df["anomaly_label"] == 1]
)

print("Unique anomaly sites:", len(anomalies))
print("Unique normal sites:", len(normal))

# --------------------------------------------------
# 3. PROJECT COORDINATES TO UTM
# --------------------------------------------------

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True
)


def get_projected_coords(data):

    x, y = transformer.transform(
        data["longitude"].to_numpy(),
        data["latitude"].to_numpy()
    )

    return np.column_stack((x, y))


copper_coords = get_projected_coords(copper)
anomaly_coords = get_projected_coords(anomalies)
normal_coords = get_projected_coords(normal)

# --------------------------------------------------
# 4. ACTUAL ANOMALY DISTANCE
# --------------------------------------------------

anomaly_tree = cKDTree(anomaly_coords)

actual_distances, _ = anomaly_tree.query(
    copper_coords,
    k=1
)

actual_mean_km = actual_distances.mean() / 1000

print("\nACTUAL ANOMALY DISTANCE")
print("Mean distance:", round(actual_mean_km, 3), "km")

# --------------------------------------------------
# 5. MONTE CARLO BASELINE
# --------------------------------------------------

rng = np.random.default_rng(42)

iterations = 10000
sample_size = len(anomalies)

baseline_means = []

for i in range(iterations):

    # Randomly select the same number of normal sites
    # as there are actual anomaly sites.

    selected_indices = rng.choice(
        len(normal_coords),
        size=sample_size,
        replace=False
    )

    selected_coords = normal_coords[selected_indices]

    tree = cKDTree(selected_coords)

    distances, _ = tree.query(
        copper_coords,
        k=1
    )

    baseline_means.append(
        distances.mean() / 1000
    )


baseline_means = np.array(baseline_means)

# --------------------------------------------------
# 6. COMPARE ACTUAL RESULT WITH NULL DISTRIBUTION
# --------------------------------------------------

null_mean = baseline_means.mean()
null_median = np.median(baseline_means)

percentile = (
    100 * np.mean(baseline_means <= actual_mean_km)
)

# One-sided empirical p-value:
# Are actual anomaly distances unusually small?

p_value = (
    1 + np.sum(baseline_means <= actual_mean_km)
) / (iterations + 1)

print("\nMONTE CARLO RESULTS")

print("Actual anomaly mean distance:",
      round(actual_mean_km, 3), "km")

print("Random baseline mean:",
      round(null_mean, 3), "km")

print("Random baseline median:",
      round(null_median, 3), "km")

print("Baseline 5th percentile:",
      round(np.percentile(baseline_means, 5), 3), "km")

print("Baseline 95th percentile:",
      round(np.percentile(baseline_means, 95), 3), "km")

print("Actual distance percentile:",
      round(percentile, 2))

print("Empirical one-sided p-value:",
      round(p_value, 4))

# --------------------------------------------------
# 7. SAVE RESULTS
# --------------------------------------------------

pd.DataFrame({
    "iteration": np.arange(1, iterations + 1),
    "random_baseline_mean_km": baseline_means
}).to_csv(
    "data/outputs/spatial_null_model_iterations.csv",
    index=False
)

pd.DataFrame({
    "metric": [
        "Actual anomaly mean distance",
        "Random baseline mean distance",
        "Random baseline median distance",
        "Random baseline 5th percentile",
        "Random baseline 95th percentile",
        "Actual distance percentile",
        "Empirical one-sided p-value"
    ],
    "value": [
        actual_mean_km,
        null_mean,
        null_median,
        np.percentile(baseline_means, 5),
        np.percentile(baseline_means, 95),
        percentile,
        p_value
    ]
}).to_csv(
    "data/outputs/spatial_null_model_summary.csv",
    index=False
)

print("\nResults saved successfully.")
