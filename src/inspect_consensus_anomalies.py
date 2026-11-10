
import pandas as pd

# Load model comparison results
df = pd.read_csv(
    "data/outputs/model_comparison_results.csv"
)

# Actual prediction column names
prediction_cols = [
    "isolation_forest",
    "lof",
    "one_class_svm"
]

# Count models flagging each observation
df["models_flagged"] = (
    df[prediction_cols] == -1
).sum(axis=1)

# Consensus: flagged by at least 2 models
consensus = df[df["models_flagged"] >= 2].copy()

# Flagged by all three models
all_three = df[df["models_flagged"] == 3].copy()

# Flagged by exactly two models
exactly_two = df[df["models_flagged"] == 2].copy()

columns = [
    "longitude",
    "latitude",
    "bouguer_anomaly",
    "magnetic_anomaly_nt",
    "elevation",
    "models_flagged"
]

print("\nCONSENSUS ANOMALIES")
print(consensus[columns].to_string(index=False))

print("\nFLAGGED BY ALL THREE MODELS:", len(all_three))
print(all_three[columns].to_string(index=False))

print("\nFLAGGED BY EXACTLY TWO MODELS:", len(exactly_two))
print(exactly_two[columns].to_string(index=False))

# Save detailed results
consensus.to_csv(
    "data/outputs/consensus_anomalies_detailed.csv",
    index=False
)

print("\nDetailed consensus results saved successfully.")
