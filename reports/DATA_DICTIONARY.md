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
- `*_mean`: arithmetic mean of repeated source rows at the same rounded coordinate.
- `*_std`, `*_min`, `*_max`: within-coordinate variability/range where available.
- `*_record_count`: number of source rows represented at that coordinate.
- `longitude_key_5dp`, `latitude_key_5dp`: rounded coordinate join keys.
