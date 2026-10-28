"""
Build docs/dashboard.html - a self-contained interactive results page.

All numbers come from results/evaluation/*.csv and from a fresh replay
simulation, so the dashboard always matches the experiments.

    python -m experiments.build_dashboard
"""

import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import (
    CORE_REGIONS,
    PERIODS,
    load_traces,
    load_workload,
    make_scheduler,
    run_simulation,
)
from experiments.evaluation import MOO_PARAMS
from sim.forecast import REALISTIC_ERROR


EVAL = os.path.join(PROJECT_ROOT, "results", "evaluation")
TEMPLATE = os.path.join(os.path.dirname(__file__), "dashboard_template.html")
OUTPUT = os.path.join(PROJECT_ROOT, "docs", "dashboard.html")

ORDER = [
    ("cost_only", "Cost Only"),
    ("round_robin", "Round Robin"),
    ("greenest_region", "Greenest Region"),
    ("greenops_spatial", "GreenOps (spatial only)"),
    ("greenops_pareto", "GreenOps Pareto"),
    ("temporal_green", "Temporal Green"),
    ("greenops_moo", "GreenOps"),
]

REPLAY = [
    ("round_robin", "Round Robin"),
    ("cost_only", "Cost Only"),
    ("greenest_region", "Greenest Region"),
    ("temporal_green", "Temporal Green"),
    ("greenops_moo", "GreenOps"),
]


def comparison():

    table = pd.read_csv(os.path.join(EVAL, "e1_main_summary.csv"))

    out = {}

    for period in ("both",) + PERIODS:

        rows = []

        for key, label in ORDER:

            r = table[(table["period"] == period) & (table["scheduler"] == key)].iloc[0]

            rows.append(dict(
                key=key,
                label=label,
                carbon=round(r["total_carbon_g_mean"] / 1000, 2),
                carbon_sd=round(r["total_carbon_g_std"] / 1000, 2),
                cost=round(r["total_cost_mean"], 1),
                sla=round(r["sla_violations_mean"], 2),
                p95=round(r["p95_latency_mean"], 2),
                latency=round(r["average_latency_mean"], 2),
                vs_rr=round(r["carbon_vs_round_robin_pct_mean"], 1),
                vs_green=round(r["carbon_vs_greenest_pct_mean"], 1),
            ))

        out[period] = rows

    return out


def traces():

    out = {}

    for period in PERIODS:

        t = load_traces(period, CORE_REGIONS)

        out[period] = {name: [round(v) for v in values[: 24 * 7]]
                       for name, values in t.items()}

    return out


def pack(rows):
    """Greedy interval packing: give overlapping jobs separate sub-rows."""

    ends = []

    for row in rows:

        start = min(row["arrival"], row["start"])

        for i, end in enumerate(ends):

            if end <= start + 1e-9:
                ends[i] = row["finish"]
                row["row"] = i
                break

        else:
            row["row"] = len(ends)
            ends.append(row["finish"])

    return len(ends)


def replay():

    workload = os.path.join(PROJECT_ROOT, "data", "workload_traces", "workload_100.csv")

    traces_winter = load_traces("winter_2024", CORE_REGIONS)

    out = {}

    for key, label in REPLAY:

        params = dict(MOO_PARAMS) if key.startswith("greenops") else {}

        summary, jobs = run_simulation(
            make_scheduler(key, max_wait=12, **params),
            traces_winter,
            load_workload(workload),
            forecast_error=REALISTIC_ERROR,
        )

        jobs = jobs[jobs["status"] == "completed"].sort_values("start_time")

        lanes = {}

        for region in CORE_REGIONS:

            rows = [
                dict(
                    id=r.job_id,
                    cls=r.flexibility,
                    arrival=round(r.arrival_time, 2),
                    start=round(r.start_time, 2),
                    finish=round(r.finish_time, 2),
                    carbon=round(r.carbon_emitted, 1),
                    late=bool(r.sla_violated),
                    cpu=int(r.cpu_required),
                )
                for r in jobs[jobs["region"] == region].itertuples()
            ]

            depth = pack(rows)

            lanes[region] = dict(rows=depth, jobs=rows)

        out[key] = dict(
            label=label,
            lanes=lanes,
            carbon=round(summary["total_carbon_g"] / 1000, 2),
            late=int(summary["sla_violations"]),
        )

    horizon = max(
        job["finish"]
        for run in out.values()
        for lane in run["lanes"].values()
        for job in lane["jobs"]
    )

    hours = int(horizon) + 2

    intensity = {name: [round(v) for v in traces_winter[name][:hours]]
                 for name in CORE_REGIONS}

    return dict(runs=out, horizon=round(horizon, 1), intensity=intensity)


def sensitivity():

    e3 = pd.read_csv(os.path.join(EVAL, "e3_forecast_summary.csv"))
    e3 = e3[e3["scenario"] == "core"]

    forecast = {}

    for variant, label in (("temporal_green", "Temporal Green"),
                           ("greenops_moo", "GreenOps"),
                           ("greenest_region", "Greenest Region")):

        sub = e3[e3["variant"] == variant].sort_values("forecast_error")

        forecast[label] = [
            [round(e * 100), round(c / 1000, 2)]
            for e, c in zip(sub["forecast_error"], sub["total_carbon_g_mean"])
        ]

    e4 = pd.read_csv(os.path.join(EVAL, "e4_maxwait_summary.csv"))
    e4 = e4[e4["scenario"] == "core"]

    maxwait = {}

    for key, label in (("temporal_green", "Temporal Green"), ("greenops_moo", "GreenOps")):

        sub = e4[e4["scheduler"] == key].sort_values("max_wait")

        maxwait[label] = dict(
            carbon=[[int(w), round(c / 1000, 2)]
                    for w, c in zip(sub["max_wait"], sub["total_carbon_g_mean"])],
            p95=[[int(w), round(p, 2)]
                 for w, p in zip(sub["max_wait"], sub["p95_latency_mean"])],
        )

    return dict(forecast=forecast, maxwait=maxwait)


def main():

    data = dict(
        comparison=comparison(),
        traces=traces(),
        replay=replay(),
        sensitivity=sensitivity(),
    )

    page = open(TEMPLATE, encoding="utf-8").read().replace(
        "__DATA__", json.dumps(data, separators=(",", ":"))
    )

    open(OUTPUT, "w", encoding="utf-8").write(page)

    print(f"Written {OUTPUT} ({len(page) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
