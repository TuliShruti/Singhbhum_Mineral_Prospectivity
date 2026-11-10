
import pandas as pd
import numpy as np

from pyproj import Transformer
from scipy.spatial import cKDTree

# 1. Load data
copper = pd.read_csv(
    "data/outputs/copper_occurrence_nearest_station_distances.csv"
)

df = pd.read_csv(
    "data/outputs/isolation_forest_results.csv"
)

# 2. Group near-duplicate coordinates consistently
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

copper = copper.dropna(
    subset=["longitude", "latitude"]
)

all_sites = unique_locations(df)

anomalies = unique_locations(
    df[df["anomaly_label"] == -1]
)

# 3. Project to UTM 45N
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True
)

def project(data):
    x, y = transformer.transform(
        data["longitude"].to_numpy(),
        data["latitude"].to_numpy()
    )
    return np.column_stack((x, y))

copper_coords = project(copper)
all_coords = project(all_sites)
anomaly_coords = project(anomalies)

# 4. Actual mean distance
actual_tree = cKDTree(anomaly_coords)

actual_distances, _ = actual_tree.query(
    copper_coords,
    k=1
)

actual_mean = actual_distances.mean() / 1000

# 5. Random baseline from ALL observation sites
rng = np.random.default_rng(42)

iterations = 10000
sample_size = len(anomaly_coords)

random_means = []

for _ in range(iterations):

    indices = rng.choice(
        len(all_coords),
        size=sample_size,
        replace=False
    )

    random_tree = cKDTree(all_coords[indices])

    distances, _ = random_tree.query(
        copper_coords,
        k=1
    )

    random_means.append(
        distances.mean() / 1000
    )

random_means = np.array(random_means)

# 6. Lower-tail test:
# Are actual anomalies unusually close?
p_value = (
    1 + np.sum(random_means <= actual_mean)
) / (iterations + 1)

percentile = (
    100 * np.mean(random_means <= actual_mean)
)

print("\nSPATIAL PERMUTATION TEST")

print("Actual anomaly mean distance:",
      round(actual_mean, 3), "km")

print("Random baseline mean:",
      round(random_means.mean(), 3), "km")

print("Random baseline median:",
      round(np.median(random_means), 3), "km")

print("Random baseline 5th percentile:",
      round(np.percentile(random_means, 5), 3), "km")

print("Random baseline 95th percentile:",
      round(np.percentile(random_means, 95), 3), "km")

print("Actual distance percentile:",
      round(percentile, 2))

print("Empirical one-sided p-value:",
      round(p_value, 4))

# 7. Save results
pd.DataFrame({
    "random_mean_distance_km": random_means
}).to_csv(
    "data/outputs/spatial_permutation_iterations.csv",
    index=False
)
