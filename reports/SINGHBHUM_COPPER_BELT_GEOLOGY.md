# Geological setting: Singhbhum Copper Belt

## Regional framework

The Singhbhum Copper Belt lies in the Precambrian eastern Indian shield, along
the Singhbhum Shear Zone (also described in the literature as the Copper Belt
Thrust or Singhbhum Thrust Belt). The shear zone is a major tectonic boundary
along the northern margin of the Singhbhum Craton and the southern part of the
North Singhbhum Mobile Belt. Its mapped trace is arcuate and its reported length
varies with the definition and extent of the mapped corridor; sources describe
segments from roughly 160 km to a regional structure approaching 200 km.

The belt is not a single uniform host-rock unit. Descriptions of the copper
district include Singhbhum Granite and soda granite, Dhanjori metavolcanic
rocks, metabasic/epidioritic rocks, and schists including chlorite-,
biotite-chlorite-, quartz-chlorite-, and quartz-sericite-bearing varieties.
This agrees broadly with the `host_rock` and `geology` text fields in the
project's occurrence inventory, but those source attributes have not yet been
independently verified against geologic mapping.

Copper mineralization is structurally associated with the shear-zone corridor.
Published descriptions report copper-bearing sulphides, particularly
chalcopyrite with pyrite and pyrrhotite, in multiple lithologies and structural
settings. The deposit-scale processes and timing are an active geological
interpretation; this project should not infer a single genesis model from
station anomalies or occurrence metadata alone.

## Relevance to this project

- The structural corridor and host-rock variation provide geological context
  for interpreting geophysical patterns and known occurrences.
- Magnetic and gravity responses are non-unique. Lithology, structure,
  alteration, topography, survey design, and processing can all affect the
  measured signal; an Isolation Forest outlier is not a copper indicator by
  itself.
- The repository currently has point occurrence attributes but no regional
  geology, mapped shear-zone, fault, or lithology layer. The geological setting
  is therefore interpretive context, not an input to the current model.
- Before spatially modeling geology, obtain an authoritative, georeferenced
  layer with scale, legend, source, and coordinate reference information, then
  validate it against the study boundary.

## Sources

1. Geological Survey of India, *The Mineral Deposits of Eastern Singhbhum and
   Surrounding Areas*, Memoirs of the Geological Survey of India. [Digitized
   catalog and chapter listing](https://southasiacommons.net/artifacts/2336602/memoirs-geological-survey-of-india/3114131/).
2. National Mineral Exploration Trust, *Proposal for General Exploration in
   the Singhbhum Copper Belt*. [Project document](https://www.nmet.gov.in/upload/project_registration/621.pdf).
3. Ghosh, R. (2022), “An overview of ore genesis in the Singhbhum Craton,
   Eastern India,” *Earth-Science Reviews*. [Article and abstract](https://doi.org/10.1016/j.earscirev.2022.103933).
4. Bhattacharyya, D.S. (1992), “Early proterozoic metallogeny, tectonics and
   geochronology of the Singhbhum Cu–U belt, eastern India,” *Precambrian
   Research*. [Article record](https://doi.org/10.1016/0301-9268(92)90113-3).

These sources differ in age, scale, and interpretive emphasis. Use the newer
reviews and exploration documentation for regional context, and consult the
original map and report metadata for locality-level claims.
