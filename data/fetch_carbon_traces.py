"""
Build hourly, historical carbon-intensity traces for the GreenOps simulator.

Sources
-------
* Germany, Norway, France, Poland
    Energy-Charts public API (Fraunhofer ISE), 15-minute generation by
    production type. Carbon intensity is derived from the generation mix
    using lifecycle emission factors (IPCC AR5 medians, the same convention
    used by Electricity Maps):

        CI(t) = sum_i P_i(t) * EF_i / sum_i P_i(t)       [gCO2eq/kWh]

* Great Britain
    National Grid ESO Carbon Intensity API - real *actual* and real
    *forecast* intensity (half-hourly). The forecast column is used to
    calibrate the forecast-error model of the simulator.

* India
    No free public hourly API exists. The trace is MODELLED from the
    Central Electricity Authority (CEA) CO2 Baseline Database (grid average
    ~0.71 tCO2/MWh) with a solar-driven midday dip, an evening peak and a
    monsoon-season reduction. It is clearly labelled `source=modelled`.

All timestamps are UTC. Hour index 0 = first hour of the period.

Usage
-----
    python data/fetch_carbon_traces.py
"""

import csv
import json
import math
import os
import random
import urllib.request
from datetime import datetime, timedelta, timezone


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(
    DATA_DIR,
    "carbon_traces",
    "historical"
)

# Two 4-week periods with very different renewable profiles.
PERIODS = {
    "winter_2024": ("2024-01-08", 28),
    "summer_2024": ("2024-07-01", 28),
}

ENERGY_CHARTS_COUNTRIES = {
    "germany": "de",
    "norway": "no",
    "france": "fr",
    "poland": "pl",
}


# ============================================================
# LIFECYCLE EMISSION FACTORS (gCO2eq / kWh)
#
# IPCC AR5 WG3 Annex III medians, as used by Electricity Maps.
# Lignite is not separated in AR5; 1,100 g/kWh is used, in line
# with German UBA estimates for lignite plants.
# ============================================================

EMISSION_FACTORS = {
    "Nuclear": 12,
    "Hydro Run-of-River": 24,
    "Hydro water reservoir": 24,
    "Hydro pumped storage": 24,
    "Biomass": 230,
    "Fossil brown coal / lignite": 1100,
    "Fossil hard coal": 820,
    "Fossil coal-derived gas": 820,
    "Fossil oil": 650,
    "Fossil gas": 490,
    "Geothermal": 38,
    "Wind onshore": 11,
    "Wind offshore": 12,
    "Solar": 45,
    "Waste": 700,
    "Others": 700,
    "Other renewables": 30,
}

# Series in the Energy-Charts response that are not generation.
NON_GENERATION = {
    "Load",
    "Residual load",
    "Renewable share of load",
    "Renewable share of generation",
    "Cross border electricity trading",
    "Hydro pumped storage consumption",
    "Load (incl. self-consumption)",
}


# ============================================================
# HTTP
# ============================================================

def fetch_json(url):

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "greenops-research/1.0"}
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%MZ")


def period_bounds(start_date, days):

    start = datetime.strptime(start_date, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )

    return start, start + timedelta(days=days)


# ============================================================
# ENERGY-CHARTS -> HOURLY CARBON INTENSITY
# ============================================================

def energy_charts_trace(country, start, end):

    url = (
        "https://api.energy-charts.info/public_power"
        f"?country={country}&start={iso(start)}&end={iso(end)}"
    )

    payload = fetch_json(url)

    timestamps = payload["unix_seconds"]

    # hour index -> [weighted emissions, generation]
    hourly = {}

    unknown = set()

    for series in payload["production_types"]:

        name = series["name"]

        if name in NON_GENERATION:
            continue

        factor = EMISSION_FACTORS.get(name)

        if factor is None:
            unknown.add(name)
            factor = 700

        for ts, value in zip(timestamps, series["data"]):

            if value is None or value <= 0:
                continue

            hour = int((ts - start.timestamp()) // 3600)

            bucket = hourly.setdefault(hour, [0.0, 0.0])

            bucket[0] += value * factor
            bucket[1] += value

    if unknown:
        print(f"    [warn] unknown production types (EF=700): {unknown}")

    total_hours = int((end - start).total_seconds() // 3600)

    trace = []

    for hour in range(total_hours):

        bucket = hourly.get(hour)

        if bucket and bucket[1] > 0:
            trace.append(bucket[0] / bucket[1])
        else:
            trace.append(None)

    return fill_gaps(trace)


# ============================================================
# NATIONAL GRID ESO (GREAT BRITAIN) - ACTUAL + FORECAST
# ============================================================

def great_britain_trace(start, end):

    actual = {}
    forecast = {}

    chunk_start = start

    # API returns at most 14 days per request.
    while chunk_start < end:

        chunk_end = min(chunk_start + timedelta(days=13), end)

        url = (
            "https://api.carbonintensity.org.uk/intensity/"
            f"{iso(chunk_start)}/{iso(chunk_end)}"
        )

        for row in fetch_json(url)["data"]:

            slot = datetime.strptime(
                row["from"], "%Y-%m-%dT%H:%MZ"
            ).replace(tzinfo=timezone.utc)

            hour = int((slot - start).total_seconds() // 3600)

            if hour < 0:
                continue

            intensity = row["intensity"]

            if intensity.get("actual") is not None:
                actual.setdefault(hour, []).append(intensity["actual"])

            if intensity.get("forecast") is not None:
                forecast.setdefault(hour, []).append(intensity["forecast"])

        chunk_start = chunk_end

    total_hours = int((end - start).total_seconds() // 3600)

    def to_list(values):
        return fill_gaps([
            sum(values[h]) / len(values[h]) if h in values else None
            for h in range(total_hours)
        ])

    return to_list(actual), to_list(forecast)


# ============================================================
# INDIA - MODELLED TRACE
# ============================================================

def india_trace(start, end, seed=7):
    """
    Modelled hourly intensity for the Indian grid.

    * Annual mean ~710 g/kWh (CEA CO2 Baseline Database v19).
    * Solar dip around 12:00 IST (UTC+5:30) - deeper in summer.
    * Evening peak (19:00-22:00 IST) served by coal/gas peakers.
    * Monsoon (July) hydro and wind lower the daily mean.
    * AR(1) noise (rho=0.85, sigma=2%) for hour-to-hour variability.
    """

    rng = random.Random(seed)

    monsoon = start.month in (6, 7, 8, 9)

    base = 650 if monsoon else 720
    solar_depth = 0.14 if monsoon else 0.10

    total_hours = int((end - start).total_seconds() // 3600)

    trace = []
    noise = 0.0

    for hour in range(total_hours):

        local = (hour + 5.5) % 24

        # Solar generation bell curve centred on 12:30 local time.
        solar = math.exp(-((local - 12.5) ** 2) / (2 * 2.2 ** 2))

        # Evening peak.
        evening = math.exp(-((local - 20.5) ** 2) / (2 * 1.5 ** 2))

        # Slight weekend demand reduction.
        weekday = (start + timedelta(hours=hour)).weekday()
        weekend = -0.02 if weekday >= 5 else 0.0

        noise = 0.85 * noise + rng.gauss(0, 0.02)

        value = base * (
            1
            - solar_depth * solar
            + 0.05 * evening
            + weekend
            + noise
        )

        trace.append(value)

    return trace


# ============================================================
# HELPERS
# ============================================================

def fill_gaps(values):
    """Linear interpolation over missing hours."""

    known = [i for i, v in enumerate(values) if v is not None]

    if not known:
        raise ValueError("trace contains no data")

    filled = list(values)

    for i, value in enumerate(values):

        if value is not None:
            continue

        left = max((k for k in known if k < i), default=None)
        right = min((k for k in known if k > i), default=None)

        if left is None:
            filled[i] = values[right]
        elif right is None:
            filled[i] = values[left]
        else:
            w = (i - left) / (right - left)
            filled[i] = values[left] * (1 - w) + values[right] * w

    return filled


def write_trace(path, start, actual, source, forecast=None):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", newline="") as file:

        writer = csv.writer(file)

        header = ["time", "timestamp_utc", "carbon_intensity"]

        if forecast is not None:
            header.append("forecast_intensity")

        header.append("source")

        writer.writerow(header)

        for hour, value in enumerate(actual):

            row = [
                hour,
                iso(start + timedelta(hours=hour)),
                round(value, 2),
            ]

            if forecast is not None:
                row.append(round(forecast[hour], 2))

            row.append(source)

            writer.writerow(row)


def describe(name, values):

    mean = sum(values) / len(values)

    print(
        f"    {name:8s} mean={mean:7.1f}  "
        f"min={min(values):7.1f}  max={max(values):7.1f}  "
        f"hours={len(values)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    for period, (start_date, days) in PERIODS.items():

        start, end = period_bounds(start_date, days)

        out_dir = os.path.join(OUTPUT_DIR, period)

        print(f"\n== {period}: {iso(start)} -> {iso(end)}")

        for region, code in ENERGY_CHARTS_COUNTRIES.items():

            trace = energy_charts_trace(code, start, end)

            write_trace(
                os.path.join(out_dir, f"{region}.csv"),
                start,
                trace,
                source="energy-charts.info (generation mix x IPCC AR5 EF)"
            )

            describe(region, trace)

        actual, forecast = great_britain_trace(start, end)

        write_trace(
            os.path.join(out_dir, "great_britain.csv"),
            start,
            actual,
            source="carbonintensity.org.uk (National Grid ESO)",
            forecast=forecast
        )

        describe("gb", actual)

        india = india_trace(start, end)

        write_trace(
            os.path.join(out_dir, "india.csv"),
            start,
            india,
            source="modelled (CEA CO2 baseline v19 calibrated)"
        )

        describe("india", india)

    print(f"\nTraces written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
