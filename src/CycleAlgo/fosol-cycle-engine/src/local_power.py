"""Load the local 2000-2026 POWER CSV as normalized environment data."""

from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path

DEFAULT_PATH = (
    Path(__file__).resolve().parents[2] / "Data" / "NASA_RAJ_DATA_2000_2026.csv"
)
SOURCE_ID = "local_power_2000_2026"
_FILL = -999.0
_VARIABLES = {
    "T2M": ("C", "Temperature at 2 Meters"),
    "QV2M": ("g/kg", "Specific Humidity at 2 Meters"),
    "GWETTOP": ("1", "MERRA-2 Surface Soil Wetness"),
    "PRECTOTCORR": ("mm/day", "Precipitation Corrected"),
}


def load_local_power(path: str | Path | None = None) -> dict:
    """Return the 2000-2026 local POWER file in the normalized E3 shape."""
    source = Path(path) if path is not None else DEFAULT_PATH
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    header_end = lines.index("-END HEADER-")
    reader = csv.reader(lines[header_end + 1 :])
    header = next(reader)
    rows = [row for row in reader if row]
    if not rows:
        raise ValueError("local POWER CSV contains no observations")
    if any(len(row) != len(header) for row in rows):
        raise ValueError("local POWER CSV contains a bad row length")

    year_index = header.index("YEAR")
    doy_index = header.index("DOY")
    variables = {
        name: {"units": units, "longname": longname}
        for name, (units, longname) in _VARIABLES.items()
    }
    observations = {}
    for row in rows:
        year = int(row[year_index])
        doy = int(row[doy_index])
        date = dt.datetime.strptime(f"{year}-{doy:03d}", "%Y-%j").date()
        values = {}
        for index, name in enumerate(header):
            if name in ("YEAR", "DOY"):
                continue
            number = float(row[index])
            values[name] = (
                None
                if not math.isfinite(number) or number in (_FILL, -9999.0)
                else number
            )
        observations[date.isoformat()] = values

    dates = sorted(observations)
    return {
        "source_id": SOURCE_ID,
        "provider": "Local POWER CSV",
        "product": "NASA POWER Daily Point (local subset)",
        "product_version": "local_2000_2026",
        "variables": variables,
        "observations": observations,
        "observation_start": dates[0],
        "observation_end": dates[-1],
        "fill_value": _FILL,
        "retrieved_at": None,
        "coverage": {
            "start_year": 2000,
            "end_year": 2026,
            "note": (
                "Local 2000-2026 subset; the 1990 file's PRECTOTCORR is "
                "excluded because it is 24x the API value."
            ),
        },
    }
