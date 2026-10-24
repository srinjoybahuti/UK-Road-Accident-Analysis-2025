"""Reproduce the whole analysis: python run_all.py  (run from the project root, inside the virtual environment)."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = ["01_inspection.py", "02_preprocessing.py", "03_eda.py", "04_cda.py", "05_summary.py"]


def main() -> int:
    t0 = time.time()
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        r = subprocess.run([sys.executable, str(ROOT / "src" / step)], cwd=ROOT)
        if r.returncode != 0:
            print(f"FAILED: {step} (exit code {r.returncode})")
            return r.returncode
    print(f"\nAll steps completed in {time.time() - t0:.0f}s. See outputs/analysis_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
