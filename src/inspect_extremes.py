
import pandas as pd

# Load integrated dataset
df = pd.read_csv("data/processed/integrated_geophysical.csv")

# Inspect the lowest and highest magnetic anomalies
print("\nLOWEST MAGNETIC ANOMALIES")

print(
    df.nsmallest(10, "magnetic_anomaly_nt")[
        ["longitude", "latitude", "magnetic_anomaly_nt",
         "bouguer_anomaly", "elevation"]
    ].to_string(index=False)
)

print("\nHIGHEST MAGNETIC ANOMALIES")

print(
    df.nlargest(10, "magnetic_anomaly_nt")[
        ["longitude", "latitude", "magnetic_anomaly_nt",
         "bouguer_anomaly", "elevation"]
    ].to_string(index=False)
)

# Inspect extreme Bouguer anomalies
print("\nLOWEST BOUGUER ANOMALIES")

print(
    df.nsmallest(10, "bouguer_anomaly")[
        ["longitude", "latitude", "bouguer_anomaly",
         "magnetic_anomaly_nt", "elevation"]
    ].to_string(index=False)
)
