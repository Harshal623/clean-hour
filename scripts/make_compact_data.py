"""Build data/compact/*.csv.gz from the full downloaded caches.

The Colab notebook needs the hourly data without a 400 MB download, so we
ship a gzipped copy of exactly the columns the analysis reads. This script
is how that copy is made, so it can be audited and rebuilt:

    python src/grids.py                  # rebuild data/grid_*.csv and data/weather_*.csv
    python scripts/make_compact_data.py   # then rebuild data/compact/*.csv.gz

Values are not rounded, resampled or filled: a row is copied as-is and
missing hours stay missing. Run from the repo root.
"""

import glob
import os
import sys

import pandas as pd

OUT = "data/compact"
WANT = {  # file stem -> columns the pipeline reads (extra columns are kept)
    "grid_pjm": ["ci", "demand_fcst"],
    "grid_ciso": ["ci", "demand_fcst"],
    "grid_erco": ["ci", "demand_fcst"],
    "grid_de": ["ci"],
    "grid_gb": ["ci", "neso_forecast"],
    "weather_pjm": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                    "cloud_cover", "shortwave_radiation"],
}


def main():
    sources = sorted(glob.glob("data/grid_*.csv") + glob.glob("data/weather_*.csv"))
    if not sources:
        sys.exit("no raw caches in data/. Run `python src/grids.py` first.")

    os.makedirs(OUT, exist_ok=True)
    made = []
    for path in sources:
        stem = os.path.basename(path)[:-4]
        d = pd.read_csv(path, index_col=0, parse_dates=True)
        need = WANT.get(stem, [])
        missing = [c for c in need if c not in d.columns]
        if missing:
            sys.exit(f"{stem}: missing required column(s) {missing}")
        if d.index.has_duplicates:
            sys.exit(f"{stem}: duplicate timestamps, refusing to ship it")
        dest = f"{OUT}/{stem}.csv.gz"
        d.to_csv(dest)
        made.append((dest, d.shape, str(d.index.min())[:16], str(d.index.max())[:16],
                     int(d.isna().sum().sum())))
        os.remove(path)  # the raw copy is hundreds of MB and is reproducible

    print(f"{'file':28s} {'shape':>12s}  {'first hour':16s}  {'last hour':16s}  NaN cells")
    for dest, shape, lo, hi, nans in made:
        print(f"{dest:28s} {str(shape):>12s}  {lo:16s}  {hi:16s}  {nans}")
    print(f"\nwrote {len(made)} files; source caches removed from data/ "
          f"(re-download with `python src/grids.py`)")


if __name__ == "__main__":
    main()
