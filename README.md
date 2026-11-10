# Singhbhum Geophysical Anomaly Analysis — Python Starter Project

## Research stage and scope

This repository is a reproducible **first-stage analysis** of the NGDR data currently available:
- Gravity observations from the 73J05 and 73J07 downloads (764 raw records).
- Ground magnetic observations from the 73J07 download (526 raw records).
- 14 copper occurrence records from the Purbi Singhbhum download.
- 1 additional copper occurrence record from 73F09 (Galudih), retained separately because it is far outside the current matched geophysical footprint.

The first experiment is **geophysical anomaly detection and spatial association with known copper occurrences**.
It is **not yet a validated supervised copper prospectivity model** and it does not claim to map the whole Subarnarekha River Basin.

The pipeline now also validates the supplied CWC basin geometry and writes
spatial coverage and occurrence-to-station distance reports. Basin containment
summaries do not imply continuous survey coverage or validate the scientific
fitness of the boundary source. See
[`reports/SINGHBHUM_COPPER_BELT_GEOLOGY.md`](reports/SINGHBHUM_COPPER_BELT_GEOLOGY.md)
for a cited geological overview and interpretation limits.

## Important verified data facts

- Gravity: 764 raw rows, 523 unique coordinate pairs.
- Magnetic: 526 raw rows, 286 unique coordinate pairs.
- Unique common gravity/magnetic coordinates: 286, after rounding longitude/latitude to 5 decimal places.
- Gravity raw coordinates span approximately 86.252–86.499°E and 22.253–22.999°N.
- Magnetic coordinates span approximately 86.256–86.499°E and 22.253–22.499°N.
- The integrated station footprint therefore follows the smaller magnetic footprint.
- The Purbi Singhbhum copper file contains 14 records. The spatial step recomputes distances from unique exact station coordinates in UTM zone 45N; use its generated summary as the current result because older checked-in distance outputs disagree.
- The 73F09 Galudih record is approximately 62.7 km from the nearest magnetic station and 53.3 km from the nearest gravity station. It is retained separately and excluded from the core spatial association analysis.
- Repeated coordinate records exist in both geophysical downloads. The pipeline aggregates at coordinate precision 5 decimal places and preserves record counts and variability statistics rather than silently discarding repeats.

## What the ML output means

The canonical `src/run_pipeline.py` pipeline applies:
1. Data validation and duplicate-aware spatial aggregation.
2. Basin geometry and coverage validation, including separation of the distant Galudih occurrence.
3. Duplicate-aware gravity/magnetic integration using five-decimal coordinate keys, retaining only shared stations covered by the main basin boundary.
4. Isolation Forest anomaly detection using magnetic anomaly, Bouguer anomaly and elevation.
5. PCA for exploratory visualization.
6. A station-point map with Purbi copper occurrences overlaid.

The `src/spatial_analysis.py` step checks CRS and geometry validity
for each CWC boundary, reports the subbasin/main-basin relationship, counts raw
and unique gravity/magnetic locations inside each boundary, summarizes station
spacing, and recomputes copper-to-nearest-station distances from the source
coordinates. Invalid geometries stop the pipeline and are not silently fixed.
Distance and area metrics use EPSG:32645 (UTM zone 45N). The analysis step
writes `reports/basin_geometry_validation.csv`,
`reports/basin_boundary_summary.csv`, `reports/basin_overlap_summary.csv`, `reports/station_coverage_summary.csv`,
`reports/copper_station_distance_summary.csv`,
`data/outputs/basin_membership_validated.csv`, and
`data/outputs/copper_nearest_station_distances_validated.csv`.

The canonical integrated file has the 24-column schema used by the anomaly and
mapping scripts. The integration step groups source records by five-decimal
coordinate keys, performs an inner gravity/magnetic join, and then retains only
matched points covered by the validated main-basin polygon. The spatial distance
report instead uses unique exact coordinate pairs so repeated source records do
not weight nearest-station distances. The Galudih (73F09) point remains a
separate comparison and is excluded from the Purbi overlay and core integration.

An Isolation Forest outlier is a **geophysical outlier relative to this dataset**. It is not proof of copper mineralisation. The anomaly score is a screening aid, not a probability of finding copper.

No synthetic negative labels are created. No supervised Random Forest/XGBoost/SVM model is trained until the occurrence inventory, study-area boundary and sampling design are adequate.

## Folder structure

```text
Singhbhum_Mineral_Prospectivity/
├── data/
│   ├── raw/          # Original prepared CSV exports; never overwrite
│   ├── processed/    # Aggregated and integrated tables
│   └── outputs/      # Model scores and spatial occurrence-distance tables
├── notebooks/
│   └── 01_quickstart.ipynb
├── src/
│   ├── audit_data.py
│   ├── integrate_data.py
│   ├── detect_anomalies.py
│   ├── make_maps.py
│   └── run_pipeline.py
├── reports/
├── figures/
├── requirements.txt
└── README.md
```

## Run in Google Colab

1. Download and extract this ZIP.
2. Upload the extracted `Singhbhum_Mineral_Prospectivity` folder to Google Drive, or upload the ZIP to Colab and extract it.
3. In Colab, change directory to the project root.
4. Run:

```bash
pip install -r requirements.txt
python src/run_pipeline.py
```

5. Inspect:
   - `reports/data_audit_summary.csv`
   - `reports/station_coverage_summary.csv`
   - `reports/copper_station_distance_summary.csv`
   - `reports/integration_quality_report.csv`
   - `data/processed/integrated_geophysical.csv`
   - `data/outputs/copper_occurrence_nearest_station_distances.csv`
   - `data/outputs/isolation_forest_anomaly_scores.csv`
   - `figures/geophysical_anomaly_occurrence_overlay.png`

## Scientific cautions / next steps

- Confirm the basin boundary and exact study-area polygon with your supervisor before describing outputs as basin-wide.
- Confirm NGDR attribute definitions, gravity units/datum/corrections, magnetic anomaly processing and survey provenance from source metadata.
- The five-decimal coordinate match is a record-matching rule, not proof that surveys were acquired at the exact same physical station. Review station IDs and duplicate rows.
- Do not interpolate beyond the data footprint. Do not interpret a point anomaly as a mineral deposit.
- The 73F09 occurrence must not be included in the core model without a spatial-coverage justification.
- Obtain additional verified occurrences and a defensible background/absence sampling strategy before supervised prospectivity modelling.
- Geological and geochemical map layers remain missing. CWC basin boundary files are present, but their provenance and suitability for the intended study area still require confirmation. The current work is a constrained geophysical pilot, not the full multi-source framework in the original proposal.
