# Data dictionary

## Gravity raw CSV
- `gid`, `objectid`: NGDR identifiers.
- `download_file`: downloaded toposheet archive identifier (73J05 or 73J07).
- `toposheet`: toposheet text in source attributes.
- `longitude`, `latitude`: geographic coordinates.
- `elevation`: source elevation field; confirm datum/units with NGDR metadata.
- `observed_gravity`, `theoretical_gravity`: source gravity fields; confirm units and reference system.
- `bouguer_anomaly`: source Bouguer anomaly; confirm reduction/datum details before geological interpretation.

## Magnetic raw CSV
- `observed_magnetic_nt`: observed magnetic field in nT, based on source field name.
- `igrf_reference_nt`: IGRF reference field in nT.
- `magnetic_anomaly_nt`: source magnetic anomaly in nT.
- `longitude`, `latitude`, `toposheet`: location/provenance.

## Copper occurrence CSV
- `locality`, `commodity`, `resource`, `grade`, `host_rock`, `geology`, `occurrence`: occurrence attributes as supplied by NGDR.
- `longitude`, `latitude`, `toposheet`: occurrence coordinates and map-sheet reference.
- Text resource/grade values are not parsed into numerical training labels in this starter project.

## Integrated data
- The canonical pipeline writes the 24-column schema consumed by `detect_anomalies.py` and `make_maps.py`.
- `*_mean`: arithmetic mean of repeated source rows at the same rounded coordinate.
- `*_std`, `*_min`, `*_max`: within-coordinate variability/range where available.
- `*_record_count`: number of source rows represented at that coordinate.
- `longitude_key_5dp`, `latitude_key_5dp`: rounded coordinate join keys. Gravity and magnetic records are inner-joined on these keys, then stations outside the validated main basin are excluded.
- `join_rule`: records the five-decimal join and main-basin containment rule.
- `integration_quality_report.csv`: number of shared stations before and after basin filtering, number excluded, and output schema width.

## Validated spatial outputs
- `basin_geometry_validation.csv`: one row per CWC boundary feature, recording source CRS, geometry type, emptiness, validity, and whether it is polygonal. Invalid, empty, null, or non-polygon geometries stop the spatial step; source geometries are never silently repaired.
- `basin_boundary_summary.csv`: boundary feature count, projected area and geographic bounds.
- `basin_overlap_summary.csv`: projected area of each basin, their intersection, the fraction of each layer covered by the other, both non-overlapping areas, and intersection-over-union.
- `station_coverage_summary.csv`: raw and exact-coordinate-unique gravity/magnetic records, containment counts/fractions for each boundary, coordinate extents, and nearest-neighbor spacing statistics.
- `copper_nearest_station_distances_validated.csv`: recomputed per-occurrence nearest-station distance for each survey, using unique exact coordinate pairs and UTM zone 45N. Precomputed distance fields from the raw occurrence export are omitted.
- `copper_station_distance_summary.csv`: per-occurrence-dataset and station-dataset distance ranges and counts within 1, 5, 10, and 25 km.
- `basin_membership_validated.csv`: point-in-main-basin and point-in-subbasin flags for all raw station and copper rows.

## Pipeline outputs
- `isolation_forest_anomaly_scores.csv`: one row per canonical integrated station, with Isolation Forest labels/scores and two PCA coordinates. These are exploratory geophysical outlier indicators, not copper probabilities or deposit predictions.
- `pca_explained_variance.csv`: explained variance ratio for each exploratory PCA component.
- `geophysical_station_occurrence_map.html`: interactive point map of integrated stations and the 14 Purbi occurrence records. Galudih (73F09) is excluded from this core overlay and is reported separately in the validated distance table.
