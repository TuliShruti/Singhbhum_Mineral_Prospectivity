
from pathlib import Path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"
BASIN = RAW / "basin"

REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "data" / "outputs"
FIGURES = ROOT / "figures"

REPORTS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

# --------------------------------------------------
# 2. LOAD BASIN BOUNDARIES
# --------------------------------------------------

main_basin = gpd.read_file(
    BASIN / "Subernarekha_Main_Basin_CWC.geojson"
)

sub_basin = gpd.read_file(
    BASIN / "Subernarekha_Subbasin.geojson"
)

print("Main basin CRS:", main_basin.crs)
print("Sub-basin CRS:", sub_basin.crs)

if main_basin.crs is None or sub_basin.crs is None:
    raise ValueError("Missing CRS in basin boundary files")

main_basin = main_basin.to_crs("EPSG:4326")
sub_basin = sub_basin.to_crs("EPSG:4326")

main_polygon = main_basin.geometry.unary_union
sub_polygon = sub_basin.geometry.unary_union

print("Main basin loaded:", len(main_basin))
print("Sub-basin loaded:", len(sub_basin))

# --------------------------------------------------
# 3. LOAD GEOPHYSICAL AND COPPER DATA
# --------------------------------------------------

gravity = pd.read_csv(
    RAW / "gravity_73J05_73J07.csv"
)

magnetic = pd.read_csv(
    RAW / "magnetic_73J07.csv"
)

copper = pd.read_csv(
    RAW / "copper_occurrences_purbi_singhbhum.csv"
)

copper_extra = pd.read_csv(
    RAW / "copper_occurrence_73F09.csv"
)

# --------------------------------------------------
# 4. CONVERT CSV DATA TO GEODATAFRAMES
# --------------------------------------------------

def make_gdf(df):

    df = df.copy()

    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"]
        ),
        crs="EPSG:4326"
    )


gravity_gdf = make_gdf(gravity)
magnetic_gdf = make_gdf(magnetic)
copper_gdf = make_gdf(copper)
copper_extra_gdf = make_gdf(copper_extra)

# --------------------------------------------------
# 5. CHECK SPATIAL MEMBERSHIP
# --------------------------------------------------

def check_membership(gdf, polygon):

    return gdf.geometry.apply(
        lambda point: polygon.covers(point)
    )


datasets = {
    "Gravity": gravity_gdf,
    "Magnetic": magnetic_gdf,
    "Copper_Purbi": copper_gdf,
    "Copper_73F09": copper_extra_gdf
}

summary = []
membership_frames = []

for name, gdf in datasets.items():

    main_mask = check_membership(
        gdf, main_polygon
    )

    sub_mask = check_membership(
        gdf, sub_polygon
    )

    unique = gdf.drop_duplicates(
        subset=["longitude", "latitude"]
    )

    unique_main = check_membership(
        unique, main_polygon
    )

    summary.append({
        "dataset": name,
        "raw_records": len(gdf),
        "unique_locations": len(unique),
        "inside_main_basin_raw": int(main_mask.sum()),
        "inside_main_basin_unique": int(unique_main.sum()),
        "inside_subbasin_raw": int(sub_mask.sum())
    })

    temp = gdf[
        ["longitude", "latitude"]
    ].copy()

    temp["dataset"] = name
    temp["inside_main_basin"] = main_mask.values
    temp["inside_subbasin"] = sub_mask.values

    membership_frames.append(temp)

# --------------------------------------------------
# 6. SAVE SPATIAL STATISTICS
# --------------------------------------------------

summary_df = pd.DataFrame(summary)

summary_df.to_csv(
    REPORTS / "basin_spatial_summary.csv",
    index=False
)

membership_df = pd.concat(
    membership_frames,
    ignore_index=True
)

membership_df.to_csv(
    OUTPUTS / "basin_membership.csv",
    index=False
)

print("\nBASIN SPATIAL SUMMARY")
print(summary_df.to_string(index=False))

# --------------------------------------------------
# 7. CREATE GEOGRAPHICAL OVERLAY MAP
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 10))

main_basin.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1.5,
    label="Main Basin"
)

sub_basin.boundary.plot(
    ax=ax,
    color="green",
    linewidth=1.5,
    label="Sub-basin"
)

gravity_gdf.plot(
    ax=ax,
    color="blue",
    markersize=8,
    label="Gravity stations"
)

magnetic_gdf.plot(
    ax=ax,
    color="orange",
    markersize=8,
    label="Magnetic stations"
)

copper_gdf.plot(
    ax=ax,
    color="red",
    marker="*",
    markersize=100,
    label="Copper occurrences"
)

copper_extra_gdf.plot(
    ax=ax,
    color="purple",
    marker="*",
    markersize=100,
    label="Additional copper occurrence"
)

ax.set_title(
    "Subarnarekha Basin: Geophysical and Copper Data",
    fontsize=14
)

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    FIGURES / "subarnarekha_basin_overlay.png",
    dpi=300
)

plt.show()

print("\nBASIN ANALYSIS COMPLETED")