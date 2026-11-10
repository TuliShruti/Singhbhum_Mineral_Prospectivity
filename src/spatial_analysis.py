"""Validate CWC basin boundaries and summarize spatial data coverage.

All distance and area calculations use EPSG:32645 (UTM zone 45N), suitable
for this local study area. Source coordinates and GeoJSON files are not edited.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.validation import explain_validity


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BASIN_DIR = RAW / "basin"
REPORTS = ROOT / "reports"
OUTPUTS = ROOT / "data" / "outputs"
METRIC_CRS = "EPSG:32645"
GEOGRAPHIC_CRS = "EPSG:4326"

REPORTS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

BASIN_FILES = {
    "main_basin": BASIN_DIR / "Subernarekha_Main_Basin_CWC.geojson",
    "subbasin": BASIN_DIR / "Subernarekha_Subbasin.geojson",
}
DATA_FILES = {
    "gravity": RAW / "gravity_73J05_73J07.csv",
    "magnetic": RAW / "magnetic_73J07.csv",
    "copper_purbi": RAW / "copper_occurrences_purbi_singhbhum.csv",
    "copper_73F09": RAW / "copper_occurrence_73F09.csv",
}


def load_and_validate_boundaries():
    """Load source boundaries, report geometry issues, and project for analysis.

    Invalid geometries are reported and cause an error. They are never silently
    repaired because a repair could alter the authoritative study boundary.
    """
    boundaries = {}
    rows = []
    has_invalid_geometry = False
    for name, path in BASIN_FILES.items():
        layer = gpd.read_file(path)
        source_crs = layer.crs
        if source_crs is None:
            raise ValueError(f"{path.name} has no CRS; cannot safely interpret coordinates")
        if layer.empty:
            raise ValueError(f"{path.name} contains no features")

        polygonal = layer.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
        valid = (
            layer.geometry.notna()
            & ~layer.geometry.is_empty
            & layer.geometry.is_valid
            & polygonal
        )
        for position, (_, feature) in enumerate(layer.iterrows()):
            geometry = feature.geometry
            rows.append({
                "boundary": name,
                "source_file": path.name,
                "feature_index": position,
                "source_crs": str(source_crs),
                "geometry_type": None if geometry is None else geometry.geom_type,
                "is_null": geometry is None,
                "is_empty": True if geometry is None else geometry.is_empty,
                "is_valid": False if geometry is None else geometry.is_valid,
                "is_polygonal": False if geometry is None else geometry.geom_type in {"Polygon", "MultiPolygon"},
                "validity_reason": "Null geometry" if geometry is None else explain_validity(geometry),
            })

        if not valid.all():
            has_invalid_geometry = True
        boundaries[name] = layer.to_crs(GEOGRAPHIC_CRS)

    validation = pd.DataFrame(rows)
    validation.to_csv(REPORTS / "basin_geometry_validation.csv", index=False)
    if has_invalid_geometry:
        raise ValueError(
            "A basin boundary has null, empty, or invalid geometry; see "
            "reports/basin_geometry_validation.csv. Source geometry was not modified."
        )

    # Dissolve features only in memory for point-in-boundary predicates.
    unions = {name: layer.geometry.unary_union for name, layer in boundaries.items()}
    return boundaries, unions, validation


def validate_boundary_relationship(boundaries, unions):
    """Summarize area and overlap of the two CWC boundary layers."""
    main_metric = gpd.GeoSeries([unions["main_basin"]], crs=GEOGRAPHIC_CRS).to_crs(METRIC_CRS).iloc[0]
    sub_metric = gpd.GeoSeries([unions["subbasin"]], crs=GEOGRAPHIC_CRS).to_crs(METRIC_CRS).iloc[0]
    intersection_area = sub_metric.intersection(main_metric).area
    sub_outside_main_area = sub_metric.difference(main_metric).area
    main_outside_sub_area = main_metric.difference(sub_metric).area
    union_area = sub_metric.union(main_metric).area
    main_area = main_metric.area
    sub_area = sub_metric.area
    pd.DataFrame([{
        "main_basin_area_km2": main_area / 1_000_000,
        "subbasin_area_km2": sub_area / 1_000_000,
        "intersection_area_km2": intersection_area / 1_000_000,
        "main_basin_area_covered_by_subbasin_percent": 100 * intersection_area / main_area if main_area else np.nan,
        "subbasin_area_within_main_basin_percent": 100 * intersection_area / sub_area if sub_area else np.nan,
        "main_basin_area_outside_subbasin_km2": main_outside_sub_area / 1_000_000,
        "subbasin_area_outside_main_basin_km2": sub_outside_main_area / 1_000_000,
        "intersection_over_union_percent": 100 * intersection_area / union_area if union_area else np.nan,
    }]).to_csv(REPORTS / "basin_overlap_summary.csv", index=False)

    rows = []
    for name, layer in boundaries.items():
        union = unions[name]
        metric = gpd.GeoSeries([union], crs=GEOGRAPHIC_CRS).to_crs(METRIC_CRS).iloc[0]
        minx, miny, maxx, maxy = layer.total_bounds
        rows.append({
            "boundary": name,
            "source_file": BASIN_FILES[name].name,
            "feature_count": len(layer),
            "crs": str(layer.crs),
            "geometry_types": ";".join(sorted(layer.geom_type.unique())),
            "is_valid": bool(layer.geometry.is_valid.all()),
            "area_km2_utm45n": metric.area / 1_000_000,
            "min_longitude": minx,
            "min_latitude": miny,
            "max_longitude": maxx,
            "max_latitude": maxy,
        })
    pd.DataFrame(rows).to_csv(REPORTS / "basin_boundary_summary.csv", index=False)
    if sub_outside_main_area > max(1.0, sub_area * 1e-6):
        print(
            "WARNING: the subbasin geometry extends beyond the main basin by "
            f"{sub_outside_main_area / 1_000_000:.3f} km². Review boundary definitions."
        )


def read_points(path):
    frame = pd.read_csv(path)
    required = {"longitude", "latitude"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name} is missing coordinate columns: {sorted(missing)}")
    coords = frame[["longitude", "latitude"]].to_numpy(dtype=float)
    if not np.isfinite(coords).all():
        raise ValueError(f"{path.name} contains missing or non-finite coordinates")
    if not frame.longitude.between(-180, 180).all() or not frame.latitude.between(-90, 90).all():
        raise ValueError(f"{path.name} contains coordinates outside longitude/latitude ranges")
    return frame


def point_membership(frame, polygon):
    points = gpd.GeoSeries(
        gpd.points_from_xy(frame.longitude, frame.latitude), crs=GEOGRAPHIC_CRS
    )
    # covers includes points exactly on the boundary.
    return points.map(polygon.covers).to_numpy(dtype=bool)


def unique_sites(frame):
    """Collapse exact duplicate coordinates for coverage and station distances."""
    return frame.drop_duplicates(["longitude", "latitude"]).copy()


def summarize_coverage(frames, unions):
    rows = []
    for name in ("gravity", "magnetic"):
        frame = frames[name]
        unique = unique_sites(frame)
        raw_main = point_membership(frame, unions["main_basin"])
        raw_sub = point_membership(frame, unions["subbasin"])
        unique_main = point_membership(unique, unions["main_basin"])
        unique_sub = point_membership(unique, unions["subbasin"])
        min_lon, min_lat = unique[["longitude", "latitude"]].min()
        max_lon, max_lat = unique[["longitude", "latitude"]].max()

        xy = project(unique)
        if len(xy) > 1:
            nearest_neighbor_km = cKDTree(xy).query(xy, k=2)[0][:, 1] / 1000
            nn_median = float(np.median(nearest_neighbor_km))
            nn_p95 = float(np.percentile(nearest_neighbor_km, 95))
            nn_max = float(np.max(nearest_neighbor_km))
        else:
            nn_median = nn_p95 = nn_max = np.nan

        rows.append({
            "dataset": name,
            "raw_records": len(frame),
            "unique_station_sites_exact_coordinates": len(unique),
            "duplicate_records": len(frame) - len(unique),
            "inside_main_basin_raw": int(raw_main.sum()),
            "outside_main_basin_raw": int((~raw_main).sum()),
            "inside_main_basin_unique": int(unique_main.sum()),
            "inside_main_basin_unique_percent": 100 * float(unique_main.mean()),
            "inside_subbasin_raw": int(raw_sub.sum()),
            "outside_subbasin_raw": int((~raw_sub).sum()),
            "inside_subbasin_unique": int(unique_sub.sum()),
            "inside_subbasin_unique_percent": 100 * float(unique_sub.mean()),
            "min_longitude": min_lon,
            "max_longitude": max_lon,
            "min_latitude": min_lat,
            "max_latitude": max_lat,
            "nearest_neighbor_median_km": nn_median,
            "nearest_neighbor_p95_km": nn_p95,
            "nearest_neighbor_max_km": nn_max,
        })
    pd.DataFrame(rows).to_csv(REPORTS / "station_coverage_summary.csv", index=False)

    membership_rows = []
    for name, frame in frames.items():
        main = point_membership(frame, unions["main_basin"])
        sub = point_membership(frame, unions["subbasin"])
        membership_rows.append(pd.DataFrame({
            "dataset": name,
            "longitude": frame.longitude.to_numpy(),
            "latitude": frame.latitude.to_numpy(),
            "inside_main_basin": main,
            "inside_subbasin": sub,
        }))
    pd.concat(membership_rows, ignore_index=True).to_csv(
        OUTPUTS / "basin_membership_validated.csv", index=False
    )


def project(frame):
    transformer = Transformer.from_crs(GEOGRAPHIC_CRS, METRIC_CRS, always_xy=True)
    x, y = transformer.transform(frame.longitude.to_numpy(), frame.latitude.to_numpy())
    return np.column_stack([x, y])


def occurrence_distances(frames):
    detail = []
    for occurrence_name in ("copper_purbi", "copper_73F09"):
        occurrences = frames[occurrence_name]
        for station_name in ("gravity", "magnetic"):
            stations = unique_sites(frames[station_name]).reset_index(drop=True)
            tree = cKDTree(project(stations))
            distances_m, indices = tree.query(project(occurrences), k=1)
            nearest = stations.iloc[indices].reset_index(drop=True)

            # Raw occurrence exports may contain precomputed distance fields from
            # an undocumented prior run. Exclude them from the validated result.
            source_distance_columns = [
                column for column in occurrences.columns
                if column.lower().startswith("nearest_")
                or column.lower().startswith("within_")
            ]
            result = occurrences.drop(columns=source_distance_columns).copy().reset_index(drop=True)
            result["occurrence_dataset"] = occurrence_name
            result["station_dataset"] = station_name
            result["nearest_station_distance_m"] = distances_m
            result["nearest_station_distance_km"] = distances_m / 1000
            result["nearest_station_longitude"] = nearest.longitude.to_numpy()
            result["nearest_station_latitude"] = nearest.latitude.to_numpy()
            if "gid" in nearest.columns:
                result["nearest_station_gid"] = nearest.gid.to_numpy()
            for threshold_km in (1, 5, 10, 25):
                result[f"within_{threshold_km}km"] = distances_m <= threshold_km * 1000
            detail.append(result)

    distances = pd.concat(detail, ignore_index=True)
    distances.to_csv(OUTPUTS / "copper_nearest_station_distances_validated.csv", index=False)
    summary = distances.groupby(
        ["occurrence_dataset", "station_dataset"], as_index=False
    ).agg(
        occurrence_count=("locality", "size"),
        nearest_distance_km=("nearest_station_distance_km", "min"),
        median_distance_km=("nearest_station_distance_km", "median"),
        maximum_distance_km=("nearest_station_distance_km", "max"),
        within_1km=("within_1km", "sum"),
        within_5km=("within_5km", "sum"),
        within_10km=("within_10km", "sum"),
        within_25km=("within_25km", "sum"),
    )
    summary.to_csv(REPORTS / "copper_station_distance_summary.csv", index=False)


def main():
    boundaries, unions, _ = load_and_validate_boundaries()
    validate_boundary_relationship(boundaries, unions)

    frames = {name: read_points(path) for name, path in DATA_FILES.items()}
    summarize_coverage(frames, unions)
    occurrence_distances(frames)
    print("Spatial analysis complete. Review basin and coverage reports under reports/.")


if __name__ == "__main__":
    main()
