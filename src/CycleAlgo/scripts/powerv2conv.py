"""Build rajshahi_climatology_v2.json from NASA POWER daily CSV.
Uses complete years 2000-2025, +/-7 day pooled window around each calendar day."""
import json, sys
import numpy as np, pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else r"Q:\CycleAlgo\Data\POWER_Point_Daily_19900101_20261023_024d38N_088d60E_LST.csv"
OUT = r"Q:\CycleAlgo\Data\rajshahi_climatology_v2.json"
Y0, Y1, HALF = 2000, 2025, 7
TMAX_THRESH = [30, 32, 34, 35, 38]

lines = open(CSV).read().splitlines()
k = next(i for i, l in enumerate(lines) if l.startswith("YEAR"))
df = pd.read_csv(CSV, skiprows=k).replace(-999, np.nan)
df = df[(df.YEAR >= Y0) & (df.YEAR <= Y1)].copy()

# this download's PRECTOTCORR is exactly 24x too large (hourly-rate scale) -> mm/day
df["PRECTOTCORR"] = df["PRECTOTCORR"] / 24.0

date = pd.to_datetime(df.YEAR.astype(str) + "-" + df.DOY.astype(str), format="%Y-%j")
# day index on a fixed leap calendar so Feb 29 is handled
df["ref"] = [pd.Timestamp(2000, d.month, d.day).dayofyear for d in date]

daily = {}
for t in pd.date_range("2000-01-01", "2000-12-31"):
    r = t.dayofyear
    diff = (df.ref - r).abs()
    diff = np.minimum(diff, 366 - diff)          # wrap around New Year
    w = df[diff <= HALF]
    q = lambda c, p: round(float(np.nanpercentile(w[c], p)), 2)
    rec = {
        "temp_mean": round(float(w.T2M.mean()), 2),
        "temp_min": q("T2M_MIN", 10),            # cold-stress bound (P10 of daily minimum)
        "temp_max": q("T2M_MAX", 90),            # heat-stress bound (P90 of daily maximum)
        "tmax_p10": q("T2M_MAX", 10), "tmax_p50": q("T2M_MAX", 50), "tmax_p90": q("T2M_MAX", 90),
        "tmin_p10": q("T2M_MIN", 10), "tmin_p50": q("T2M_MIN", 50), "tmin_p90": q("T2M_MIN", 90),
        "gwettop_mean": round(float(w.GWETTOP.mean()), 2),
        "precip_mean": round(float(w.PRECTOTCORR.mean()), 2),
        "n_samples": int(len(w)),
    }
    for th in TMAX_THRESH:
        rec[f"p_tmax_gt_{th}"] = round(float((w.T2M_MAX > th).mean()), 3)
    daily[t.strftime("%m-%d")] = rec

json.dump({"metadata": {
    "source": "NASA POWER (MERRA-2) daily point data",
    "location": "Rajshahi", "lat": 24.3769, "lon": 88.6031,
    "years": f"{Y0}-{Y1}", "window_days": f"+/-{HALF}",
    "notes": "temp_mean=mean T2M; temp_max=P90 of T2M_MAX; temp_min=P10 of T2M_MIN; p_tmax_gt_X=share of window-days with Tmax>X C"},
    "daily": daily}, open(OUT, "w"), indent=1)
print("wrote", OUT, len(daily), "days")