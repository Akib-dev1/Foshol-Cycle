import pandas as pd
import json
from datetime import date, timedelta

# 1. Read the CSV, skipping the 12 lines of NASA text header at the top
df = pd.read_csv(r"Q:\CycleAlgo\Data\NASA_RAJ_DATA_2000_2026.csv", skiprows=12)

# 2. Remove rows where NASA had missing satellite data (-999.0)
df = df[df["T2M"] != -999.0].copy()

# 3. Convert YEAR + DOY (Day of Year, 1..366) into "MM-DD" strings (e.g., "12-10")
def to_mmdd(row):
    d = date(int(row["YEAR"]), 1, 1) + timedelta(days=int(row["DOY"]) - 1)
    return d.strftime("%m-%d")

df["mmdd"] = df.apply(to_mmdd, axis=1)

# 4. Group all 26 years by "MM-DD" to get daily mean, min, and max temperatures
grouped = df.groupby("mmdd").agg(
    temp_mean=("T2M", lambda x: round(x.mean(), 2)),
    temp_min=("T2M", lambda x: round(x.min(), 2)),
    temp_max=("T2M", lambda x: round(x.max(), 2)),
    gwettop_mean=("GWETTOP", lambda x: round(x.mean(), 2)),
    precip_mean=("PRECTOTCORR", lambda x: round(x.mean(), 2))
).to_dict(orient="index")

# 5. Save the clean JSON file
output = {
    "metadata": {"source": "NASA POWER 2000-2026 Climatology", "location": "Rajshahi"},
    "daily": grouped
}

with open(r"Q:\CycleAlgo\Data\rajshahi_nasa_project_ready.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("Saved rajshahi_nasa_project_ready.json successfully!")