
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. PROJECT PATHS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"

FIGURES.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

# ==========================================
# 2. LOAD INTEGRATED DATASET
# ==========================================

df = pd.read_csv(
    DATA / "integrated_geophysical.csv"
)

print("\nDATASET INFORMATION")
print(df.info())

print("\nSTATISTICAL SUMMARY")
print(df.describe().T)

# ==========================================
# 3. SELECT GEOLOGICAL FEATURES
# ==========================================

features = [
    "bouguer_anomaly",
    "magnetic_anomaly_nt",
    "elevation"
]

X = df[features]

# Save descriptive statistics
X.describe().T.to_csv(
    REPORTS / "feature_statistics.csv"
)

# ==========================================
# 4. FEATURE DISTRIBUTIONS
# ==========================================

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, feature in zip(axes, features):

    ax.hist(
        X[feature],
        bins=25,
        edgecolor="black",
        alpha=0.8
    )

    ax.set_title(feature.replace("_", " ").title())
    ax.set_xlabel(feature)
    ax.set_ylabel("Frequency")
    ax.grid(alpha=0.2)

plt.tight_layout()

plt.savefig(
    FIGURES / "feature_distributions.png",
    dpi=300
)

plt.close()

# ==========================================
# 5. BOXPLOTS
# ==========================================

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, feature in zip(axes, features):

    ax.boxplot(X[feature].dropna())

    ax.set_title(feature.replace("_", " ").title())
    ax.set_ylabel("Value")
    ax.grid(alpha=0.2)

plt.tight_layout()

plt.savefig(
    FIGURES / "feature_boxplots.png",
    dpi=300
)

plt.close()

# ==========================================
# 6. CORRELATION MATRIX
# ==========================================

correlation = X.corr(method="pearson")

print("\nCORRELATION MATRIX")
print(correlation)

correlation.to_csv(
    REPORTS / "correlation_matrix.csv"
)

fig, ax = plt.subplots(figsize=(8, 6))

im = ax.imshow(
    correlation,
    cmap="coolwarm",
    vmin=-1,
    vmax=1
)

ax.set_xticks(range(len(features)))
ax.set_yticks(range(len(features)))

ax.set_xticklabels(features, rotation=30, ha="right")
ax.set_yticklabels(features)

for i in range(len(features)):
    for j in range(len(features)):

        ax.text(
            j, i,
            f"{correlation.iloc[i, j]:.2f}",
            ha="center",
            va="center"
        )

plt.colorbar(im, ax=ax, label="Pearson correlation")

ax.set_title("Geophysical Feature Correlation")

plt.tight_layout()

plt.savefig(
    FIGURES / "correlation_heatmap.png",
    dpi=300
)

plt.close()

# ==========================================
# 7. GRAVITY VS MAGNETIC SCATTER PLOT
# ==========================================

fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(
    df["bouguer_anomaly"],
    df["magnetic_anomaly_nt"],
    alpha=0.7
)

ax.set_xlabel("Bouguer Anomaly")
ax.set_ylabel("Magnetic Anomaly (nT)")

ax.set_title("Gravity vs Magnetic Anomaly")

ax.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    FIGURES / "gravity_magnetic_scatter.png",
    dpi=300
)

plt.close()

# ==========================================
# 8. SPATIAL DISTRIBUTION
# ==========================================

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sc1 = axes[0].scatter(
    df["longitude"],
    df["latitude"],
    c=df["bouguer_anomaly"],
    cmap="coolwarm",
    s=25
)

axes[0].set_title("Bouguer Anomaly Distribution")
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")

plt.colorbar(sc1, ax=axes[0], label="Bouguer anomaly")

sc2 = axes[1].scatter(
    df["longitude"],
    df["latitude"],
    c=df["magnetic_anomaly_nt"],
    cmap="viridis",
    s=25
)

axes[1].set_title("Magnetic Anomaly Distribution")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")

plt.colorbar(sc2, ax=axes[1], label="Magnetic anomaly (nT)")

plt.tight_layout()

plt.savefig(
    FIGURES / "geophysical_feature_maps.png",
    dpi=300
)

plt.close()

print("\nEDA COMPLETED SUCCESSFULLY")

print("\nGenerated files:")
print("1. feature_distributions.png")
print("2. feature_boxplots.png")
print("3. correlation_heatmap.png")
print("4. gravity_magnetic_scatter.png")
print("5. geophysical_feature_maps.png")
