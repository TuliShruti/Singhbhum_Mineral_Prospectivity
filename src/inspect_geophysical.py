
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASIN = RAW / "basin"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "data" / "outputs"

# Load datasets
gravity = pd.read_csv(RAW / "gravity_73J05_73J07.csv")
magnetic = pd.read_csv(RAW / "magnetic_73J07.csv")

main_basin = gpd.read_file(
    BASIN / "Subernarekha_Main_Basin_CWC.geojson"
).to_crs("EPSG:4326")

polygon = main_basin.geometry.union_all()

# Filter observations inside the basin
def filter_inside(df):
    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(
            df.longitude, df.latitude
        ),
        crs="EPSG:4326"
    )
    return gdf[gdf.geometry.apply(polygon.covers)].copy()

gravity = filter_inside(gravity)
magnetic = filter_inside(magnetic)

# ------------------------------------------------
# 1. DUPLICATE COORDINATE INVESTIGATION
# ------------------------------------------------

def duplicate_analysis(df, name, measurement_columns):

    grouped = df.groupby(
        ["longitude", "latitude"]
    )

    result = grouped.agg(
        record_count=("longitude", "size")
    )

    for col in measurement_columns:
        result[f"{col}_unique_values"] = grouped[col].nunique()
        result[f"{col}_mean"] = grouped[col].mean()
        result[f"{col}_std"] = grouped[col].std()

    result = result.reset_index()

    result.to_csv(
        OUTPUTS / f"{name}_duplicate_analysis.csv",
        index=False
    )

    print(f"\n{name} duplicate analysis")
    print("Unique coordinates:", len(result))
    print("Repeated coordinates:",
          int((result.record_count > 1).sum()))

    return result

gravity_dup = duplicate_analysis(
    gravity,
    "gravity",
    ["bouguer_anomaly", "elevation"]
)

magnetic_dup = duplicate_analysis(
    magnetic,
    "magnetic",
    ["magnetic_anomaly_nt"]
)

# ------------------------------------------------
# 2. EXACT COORDINATE OVERLAP
# ------------------------------------------------

g_coords = set(
    zip(gravity.longitude.round(6),
        gravity.latitude.round(6))
)

m_coords = set(
    zip(magnetic.longitude.round(6),
        magnetic.latitude.round(6))
)

common = g_coords.intersection(m_coords)

print("\nEXACT COORDINATE OVERLAP")
print("Gravity unique locations:", len(g_coords))
print("Magnetic unique locations:", len(m_coords))
print("Shared coordinates:", len(common))

# ------------------------------------------------
# 3. NEAREST STATION DISTANCES
# ------------------------------------------------

# UTM Zone 45N: distances in metres
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32645",
    always_xy=True
)

def project_coordinates(df):
    x, y = transformer.transform(
        df.longitude.to_numpy(),
        df.latitude.to_numpy()
    )
    return np.column_stack([x, y])

g_unique = gravity.drop_duplicates(
    ["longitude", "latitude"]
)

m_unique = magnetic.drop_duplicates(
    ["longitude", "latitude"]
)

g_xy = project_coordinates(g_unique)
m_xy = project_coordinates(m_unique)

tree = cKDTree(m_xy)

distances, indices = tree.query(g_xy, k=1)

nearest = pd.DataFrame({
    "gravity_longitude": g_unique.longitude.to_numpy(),
    "gravity_latitude": g_unique.latitude.to_numpy(),
    "nearest_magnetic_longitude": m_unique.longitude.to_numpy()[indices],
    "nearest_magnetic_latitude": m_unique.latitude.to_numpy()[indices],
    "distance_km": distances / 1000
})

nearest.to_csv(
    OUTPUTS / "gravity_magnetic_nearest_distances.csv",
    index=False
)

print("\nNEAREST STATION DISTANCE")
print(nearest.distance_km.describe())

print("\nAll analyses completed.")
