
import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv(
    "data/outputs/model_comparison_results.csv"
)

# Actual prediction column names
models = {
    "Isolation Forest": "isolation_forest",
    "Local Outlier Factor": "lof",
    "One-Class SVM": "one_class_svm"
}

# Calculate consensus count
df["models_flagged"] = (
    df[list(models.values())] == -1
).sum(axis=1)

# Create 4 maps
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
axes = axes.flatten()

# Individual model maps
for i, (model_name, column) in enumerate(models.items()):

    normal = df[df[column] == 1]
    anomaly = df[df[column] == -1]

    axes[i].scatter(
        normal["longitude"],
        normal["latitude"],
        c="lightgray",
        s=15,
        label="Normal"
    )

    axes[i].scatter(
        anomaly["longitude"],
        anomaly["latitude"],
        c="red",
        s=35,
        marker="*",
        label="Anomaly"
    )

    axes[i].set_title(model_name)
    axes[i].set_xlabel("Longitude")
    axes[i].set_ylabel("Latitude")
    axes[i].legend()
    axes[i].grid(alpha=0.2)

# Consensus map
consensus = df[df["models_flagged"] >= 2]

axes[3].scatter(
    df["longitude"],
    df["latitude"],
    c="lightgray",
    s=15,
    label="Other observations"
)

axes[3].scatter(
    consensus["longitude"],
    consensus["latitude"],
    c="blue",
    s=45,
    marker="*",
    label="Consensus anomaly"
)

axes[3].set_title("Consensus Anomalies")
axes[3].set_xlabel("Longitude")
axes[3].set_ylabel("Latitude")
axes[3].legend()
axes[3].grid(alpha=0.2)

plt.tight_layout()

plt.savefig(
    "figures/model_agreement_map.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Map saved: figures/model_agreement_map.png")
