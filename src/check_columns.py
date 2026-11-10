
import pandas as pd

df = pd.read_csv(
    "data/outputs/model_comparison_results.csv"
)

print("Available columns:")
for col in df.columns:
    print(col)
