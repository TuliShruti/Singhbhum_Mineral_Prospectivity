from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
steps = [
    "audit_data.py",
    "spatial_analysis.py",
    "integrate_data.py",
    "detect_anomalies.py",
    "make_maps.py",
]
for step in steps:
    print(f"\n===== Running {step} =====", flush=True)
    subprocess.run([sys.executable, str(ROOT / "src" / step)], check=True)
print("\nPIPELINE FINISHED. See reports/, data/processed/, data/outputs/ and figures/.")
