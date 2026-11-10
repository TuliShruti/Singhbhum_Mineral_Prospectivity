from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

g = pd.read_csv(RAW / "gravity_73J05_73J07.csv")
m = pd.read_csv(RAW / "magnetic_73J07.csv")

# Five decimal places are used only to reconcile repeated/exported station coordinates.
# Original source coordinate values remain represented by the rounded key.
for frame in (g, m):
    frame["lon_key"] = frame["longitude"].round(5)
    frame["lat_key"] = frame["latitude"].round(5)

def unique_text(series):
    vals = sorted(set(series.dropna().astype(str)))
    return ";".join(vals)

g_agg = g.groupby(["lon_key", "lat_key"], as_index=False).agg(
    longitude=("longitude", "mean"),
    latitude=("latitude", "mean"),
    gravity_record_count=("gid", "count"),
    gravity_toposheets=("toposheet", unique_text),
    elevation_mean=("elevation", "mean"),
    elevation_std=("elevation", "std"),
    observed_gravity_mean=("observed_gravity", "mean"),
    theoretical_gravity_mean=("theoretical_gravity", "mean"),
    bouguer_anomaly_mean=("bouguer_anomaly", "mean"),
    bouguer_anomaly_std=("bouguer_anomaly", "std"),
    bouguer_anomaly_min=("bouguer_anomaly", "min"),
    bouguer_anomaly_max=("bouguer_anomaly", "max"),
)
m_agg = m.groupby(["lon_key", "lat_key"], as_index=False).agg(
    magnetic_record_count=("gid", "count"),
    magnetic_toposheets=("toposheet", unique_text),
    observed_magnetic_nt_mean=("observed_magnetic_nt", "mean"),
    igrf_reference_nt_mean=("igrf_reference_nt", "mean"),
    magnetic_anomaly_nt_mean=("magnetic_anomaly_nt", "mean"),
    magnetic_anomaly_nt_std=("magnetic_anomaly_nt", "std"),
    magnetic_anomaly_nt_min=("magnetic_anomaly_nt", "min"),
    magnetic_anomaly_nt_max=("magnetic_anomaly_nt", "max"),
)
integrated = m_agg.merge(g_agg, on=["lon_key", "lat_key"], how="inner", validate="one_to_one")
integrated = integrated.rename(columns={"lon_key": "longitude_key_5dp", "lat_key": "latitude_key_5dp"})
integrated["coordinate_system"] = "EPSG:4326"
integrated["join_rule"] = "Inner join on longitude/latitude rounded to 5 decimal places"

if integrated.empty:
    raise RuntimeError("No common gravity/magnetic stations found.")
integrated.to_csv(PROC / "integrated_geophysical.csv", index=False)

print("Integrated geophysical dataset:", integrated.shape)
print("Columns:", integrated.columns.tolist())
print(integrated.head().to_string(index=False))
