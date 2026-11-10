
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/integrated_geophysical.csv")

# Plot magnetic anomaly at each observation location
plt.figure(figsize=(10, 7))

sc = plt.scatter(
    df["longitude"],
    df["latitude"],
    c=df["magnetic_anomaly_nt"],
    cmap="RdBu_r",
    s=45,
    edgecolors="black",
    linewidths=0.3
)

plt.colorbar(sc, label="Magnetic anomaly (nT)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Spatial Distribution of Magnetic Anomalies")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("figures/magnetic_spatial_check.png", dpi=300)
plt.show()

# Print percentile values
print("\nMAGNETIC ANOMALY PERCENTILES")
print(
    df["magnetic_anomaly_nt"].quantile(
        [0, 0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1]
    )
)

# Count extreme observations
print("\nEXTREME VALUE COUNTS")
print("Below -500 nT:", (df["magnetic_anomaly_nt"] < -500).sum())
print("Above +500 nT:", (df["magnetic_anomaly_nt"] > 500).sum())

print("\nSPATIAL MAP SAVED")
