from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "outputs"
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

scores = pd.read_csv(OUT / "isolation_forest_anomaly_scores.csv")
copper = pd.read_csv(RAW / "copper_occurrences_purbi_singhbhum.csv")

# Static map: station observations and occurrence points only; no interpolation or basin boundary implied.
fig, ax = plt.subplots(figsize=(10, 8))
sc = ax.scatter(
    scores["longitude"], scores["latitude"],
    c=scores["anomaly_score"], cmap="viridis",
    s=24, alpha=0.8, label="Integrated geophysical stations"
)
ax.scatter(
    copper["longitude"], copper["latitude"],
    marker="*", s=130, edgecolors="black", linewidths=0.6,
    color="red", label="Documented copper occurrences"
)
for _, row in copper.iterrows():
    ax.annotate(str(row["locality"]), (row["longitude"], row["latitude"]),
                xytext=(3, 3), textcoords="offset points", fontsize=7)
cbar = fig.colorbar(sc, ax=ax)
cbar.set_label("Isolation Forest anomaly score (higher = more unusual)")
ax.set_xlabel("Longitude (degrees, EPSG:4326)")
ax.set_ylabel("Latitude (degrees, EPSG:4326)")
ax.set_title("Geophysical Anomaly Scores and Copper Occurrence Overlay\n(Station points; not a continuous prospectivity surface)")
ax.legend(loc="best")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(FIG / "geophysical_anomaly_occurrence_overlay.png", dpi=220)
plt.close(fig)

# Feature distributions
features = ["magnetic_anomaly_nt_mean", "bouguer_anomaly_mean", "elevation_mean"]
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, col in zip(axes, features):
    ax.hist(scores[col].dropna(), bins=25, edgecolor="black", alpha=0.8)
    ax.set_title(col.replace("_", " "))
    ax.set_ylabel("Station count")
fig.tight_layout()
fig.savefig(FIG / "feature_distributions.png", dpi=200)
plt.close(fig)

# Interactive point map
center = [scores["latitude"].mean(), scores["longitude"].mean()]
mp = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
station_group = folium.FeatureGroup(name="Geophysical stations")
for _, row in scores.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=3,
        color="#2457A6",
        fill=True,
        fill_opacity=0.65,
        popup=(f"Anomaly score: {row['anomaly_score']:.4f}<br>"
               f"Magnetic anomaly: {row['magnetic_anomaly_nt_mean']:.2f} nT<br>"
               f"Bouguer anomaly: {row['bouguer_anomaly_mean']:.2f}")
    ).add_to(station_group)
station_group.add_to(mp)

occ_group = folium.FeatureGroup(name="Copper occurrences")
for _, row in copper.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
        tooltip=str(row["locality"]),
        popup=f"{row['locality']} | {row['commodity']} | Toposheet {row['toposheet']}",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(occ_group)
occ_group.add_to(mp)
folium.LayerControl().add_to(mp)
mp.save(OUT / "geophysical_station_occurrence_map.html")

print("Maps saved to figures/ and data/outputs/.")
