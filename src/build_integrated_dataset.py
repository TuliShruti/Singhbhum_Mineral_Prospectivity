
from pathlib import Path
import pandas as pd
import geopandas as gpd

# ==========================================
# 1. PROJECT PATHS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"
BASIN = RAW / "basin"

PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

PROCESSED.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. LOAD DATA
# ==========================================

gravity = pd.read_csv(
    RAW / "gravity_73J05_73J07.csv"
)

magnetic = pd.read_csv(
    RAW / "magnetic_73J07.csv"
)

basin = gpd.read_file(
    BASIN / "Subernarekha_Main_Basin_CWC.geojson"
).to_crs("EPSG:4326")

polygon = basin.geometry.union_all()

# ==========================================
# 3. FILTER DATA INSIDE BASIN
# ==========================================

def filter_inside(df):

    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"]
        ),
        crs="EPSG:4326"
    )

    mask = gdf.geometry.apply(polygon.covers)

    return pd.DataFrame(
        gdf.loc[mask].drop(columns="geometry")
    )

gravity = filter_inside(gravity)
magnetic = filter_inside(magnetic)

# ==========================================
# 4. NORMALIZE COORDINATE PRECISION
# ==========================================

def prepare_coordinates(df):

    df = df.copy()

    df["lon_key"] = df["longitude"].round(6)
    df["lat_key"] = df["latitude"].round(6)

    return df

gravity = prepare_coordinates(gravity)
magnetic = prepare_coordinates(magnetic)

# ==========================================
# 5. AGGREGATE GRAVITY DATA
# ==========================================

gravity_grouped = (
    gravity.groupby(["lon_key", "lat_key"])
    .agg(
        gravity_record_count=("bouguer_anomaly", "size"),

        longitude=("longitude", "mean"),
        latitude=("latitude", "mean"),

        bouguer_anomaly=(
            "bouguer_anomaly", "mean"
        ),

        gravity_bouguer_std=(
            "bouguer_anomaly", "std"
        ),

        elevation=(
            "elevation", "mean"
        ),

        gravity_elevation_std=(
            "elevation", "std"
        )
    )
    .reset_index()
)

# ==========================================
# 6. AGGREGATE MAGNETIC DATA
# ==========================================

magnetic_grouped = (
    magnetic.groupby(["lon_key", "lat_key"])
    .agg(
        magnetic_record_count=(
            "magnetic_anomaly_nt", "size"
        ),

        magnetic_anomaly_nt=(
            "magnetic_anomaly_nt", "mean"
        ),

        magnetic_anomaly_std=(
            "magnetic_anomaly_nt", "std"
        )
    )
    .reset_index()
)

# ==========================================
# 7. INTEGRATE BOTH DATASETS
# ==========================================

integrated = pd.merge(
    gravity_grouped,
    magnetic_grouped,
    on=["lon_key", "lat_key"],
    how="inner",
    validate="one_to_one"
)

# ==========================================
# 8. HANDLE SINGLE-RECORD STD VALUES
# ==========================================

std_columns = [
    "gravity_bouguer_std",
    "gravity_elevation_std",
    "magnetic_anomaly_std"
]

integrated[std_columns] = (
    integrated[std_columns].fillna(0)
)

# ==========================================
# 9. REMOVE INTERNAL JOIN KEYS
# ==========================================

integrated.drop(
    columns=["lon_key", "lat_key"],
    inplace=True
)

# ==========================================
# 10. SAVE INTEGRATED DATASET
# ==========================================

output_file = (
    PROCESSED / "integrated_geophysical.csv"
)

integrated.to_csv(
    output_file,
    index=False
)

# ==========================================
# 11. SAVE QUALITY CONTROL REPORT
# ==========================================

quality_report = pd.DataFrame({
    "metric": [
        "Gravity basin unique coordinates",
        "Magnetic basin unique coordinates",
        "Integrated shared coordinates",
        "Gravity records used",
        "Magnetic records used"
    ],

    "value": [
        gravity_grouped.shape[0],
        magnetic_grouped.shape[0],
        integrated.shape[0],
        len(gravity),
        len(magnetic)
    ]
})

quality_report.to_csv(
    REPORTS / "integration_quality_report.csv",
    index=False
)

# ==========================================
# 12. DISPLAY RESULTS
# ==========================================

print("\nINTEGRATION COMPLETED")

print("\nGravity locations:", len(gravity_grouped))
print("Magnetic locations:", len(magnetic_grouped))

print(
    "Integrated locations:",
    len(integrated)
)

print("\nIntegrated dataset columns:")
print(integrated.columns.tolist())

print("\nFirst five rows:")
print(integrated.head())

print("\nMissing values:")
print(integrated.isnull().sum())

print("\nSaved:", output_file)
