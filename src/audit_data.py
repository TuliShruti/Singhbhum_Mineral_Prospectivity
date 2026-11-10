from pathlib import Path
import pandas as pd
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "data" / "outputs"
REPORTS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

gravity = pd.read_csv(RAW / "gravity_73J05_73J07.csv")
magnetic = pd.read_csv(RAW / "magnetic_73J07.csv")
copper = pd.read_csv(RAW / "copper_occurrences_purbi_singhbhum.csv")
copper_73f09 = pd.read_csv(RAW / "copper_occurrence_73F09.csv")

required = {
    "gravity": {"longitude", "latitude", "bouguer_anomaly", "elevation"},
    "magnetic": {"longitude", "latitude", "magnetic_anomaly_nt"},
    "copper": {"longitude", "latitude", "locality", "commodity"},
}
for name, frame in [("gravity", gravity), ("magnetic", magnetic), ("copper", copper)]:
    missing = required[name] - set(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing required columns: {sorted(missing)}")
    if frame[["longitude", "latitude"]].isna().any().any():
        raise ValueError(f"{name} has missing coordinates")
    if not frame["longitude"].between(-180, 180).all():
        raise ValueError(f"{name} longitude outside valid range")
    if not frame["latitude"].between(-90, 90).all():
        raise ValueError(f"{name} latitude outside valid range")

def unique_coords(df):
    return df[["longitude", "latitude"]].round(5).drop_duplicates()

gxy = unique_coords(gravity)
mxy = unique_coords(magnetic)
common = gxy.merge(mxy, on=["longitude", "latitude"], how="inner")

summary = pd.DataFrame([
    ["gravity", len(gravity), len(gxy), int(gravity.duplicated(["longitude", "latitude"]).sum()),
     gravity.longitude.min(), gravity.longitude.max(), gravity.latitude.min(), gravity.latitude.max()],
    ["magnetic", len(magnetic), len(mxy), int(magnetic.duplicated(["longitude", "latitude"]).sum()),
     magnetic.longitude.min(), magnetic.longitude.max(), magnetic.latitude.min(), magnetic.latitude.max()],
    ["copper_purbi", len(copper), len(copper), 0,
     copper.longitude.min(), copper.longitude.max(), copper.latitude.min(), copper.latitude.max()],
    ["copper_73F09", len(copper_73f09), len(copper_73f09), 0,
     copper_73f09.longitude.min(), copper_73f09.longitude.max(), copper_73f09.latitude.min(), copper_73f09.latitude.max()],
], columns=["dataset", "raw_records", "unique_coordinate_pairs", "duplicate_coordinate_rows",
            "min_lon", "max_lon", "min_lat", "max_lat"])
summary.to_csv(REPORTS / "data_audit_summary.csv", index=False)

# Metric nearest-neighbour distances: UTM zone 45N is appropriate for this eastern India study area.
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32645", always_xy=True)
gx, gy = transformer.transform(gravity.longitude.to_numpy(), gravity.latitude.to_numpy())
mx, my = transformer.transform(magnetic.longitude.to_numpy(), magnetic.latitude.to_numpy())
g_tree = cKDTree(np.column_stack([gx, gy]))
m_tree = cKDTree(np.column_stack([mx, my]))

def add_distances(frame, name):
    x, y = transformer.transform(frame.longitude.to_numpy(), frame.latitude.to_numpy())
    dg, ig = g_tree.query(np.column_stack([x, y]))
    dm, im = m_tree.query(np.column_stack([x, y]))
    out = frame.copy()
    out["nearest_gravity_distance_km"] = dg / 1000
    out["nearest_magnetic_distance_km"] = dm / 1000
    out["within_1km_gravity"] = dg <= 1000
    out["within_1km_magnetic"] = dm <= 1000
    out["within_5km_gravity"] = dg <= 5000
    out["within_5km_magnetic"] = dm <= 5000
    out.to_csv(OUTPUTS / name, index=False)
    return out

purbi_dist = add_distances(copper, "copper_occurrence_nearest_station_distances.csv")
galudih_dist = add_distances(copper_73f09, "copper_73F09_nearest_station_distances.csv")

print("DATA AUDIT COMPLETE")
print(summary.to_string(index=False))
print(f"\nUnique common gravity/magnetic coordinates: {len(common)}")
print(f"Purbi copper records within 1 km of magnetic stations: {purbi_dist.within_1km_magnetic.sum()} / {len(purbi_dist)}")
print(f"Purbi copper records within 5 km of magnetic stations: {purbi_dist.within_5km_magnetic.sum()} / {len(purbi_dist)}")
print("\nNearest distances (km):")
print(purbi_dist[["locality", "nearest_gravity_distance_km", "nearest_magnetic_distance_km"]].round(2).to_string(index=False))
print("\n73F09 occurrence:")
print(galudih_dist[["locality", "nearest_gravity_distance_km", "nearest_magnetic_distance_km"]].round(2).to_string(index=False))
