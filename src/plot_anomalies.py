
import pandas as pd
import matplotlib.pyplot as plt

# Load Isolation Forest results
df = pd.read_csv(
    "data/outputs/isolation_forest_results.csv"
)

normal = df[df["anomaly_label"] == 1]
anomalies = df[df["anomaly_label"] == -1]

plt.figure(figsize=(11, 8))

# Plot normal observations
plt.scatter(
    normal["longitude"],
    normal["latitude"],
    c="lightgrey",
    s=35,
    label="Normal observations",
    edgecolors="black",
    linewidths=0.3
)

# Plot anomalous observations
sc = plt.scatter(
    anomalies["longitude"],
    anomalies["latitude"],
    c=anomalies["anomaly_score"],
    cmap="Reds_r",
    s=100,
    marker="*",
    edgecolors="black",
    linewidths=0.6,
    label="Anomalous observations"
)

plt.colorbar(
    sc,
    label="Isolation Forest anomaly score"
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Isolation Forest - Geophysical Anomaly Locations")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "figures/isolation_forest_anomaly_map.png",
    dpi=300
)

plt.show()

print("Total observations:", len(df))
print("Anomalies:", len(anomalies))
print("Anomaly map generated successfully.")
