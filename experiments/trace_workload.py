"""
Trace-driven workloads from the Alibaba Cluster Trace v2018.

Arrival times, runtimes and CPU demand come from the real trace
(data/workload_traces/alibaba_jobs.csv.gz, built by prepare_alibaba.py).
The trace has no notion of deadlines, budgets or data placement, so
these are ANNOTATED synthetically (as in Wiesner et al. [17], who also
assign flexibility windows to real job traces):

    class      share  deadline slack        carbon priority  budget x
    strict     30 %   0.25 - 1 h            0.2 - 0.6        1.3 - 2.2
    batch      40 %   2 - 8 h               0.5 - 0.8        1.1 - 2.0
    flexible   30 %   8 - 24 h              0.7 - 1.0        1.05 - 1.9

    home region   uniform over the regions (tenants spread evenly)
    budget        multiple of the job's compute cost in its HOME region
    pinned        `locality_fraction` of jobs may only run at home
    data size     cpu x runtime_h x `gb_per_core_hour` x LogNormal(0, 1)

Each seed draws an independent random sample of `fraction` of the
trace's jobs and offsets it by (seed mod 3) weeks into the carbon trace,
so different seeds see different weeks of grid conditions.
"""

import os

import numpy as np
import pandas as pd

from sim.job import Job


TRACE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "data",
    "workload_traces",
    "alibaba_jobs.csv.gz",
)

REGION_PRICES = {
    "India": 0.08,
    "Germany": 0.11,
    "Norway": 0.14,
    "France": 0.12,
    "Poland": 0.09,
    "Great Britain": 0.13,
}

CLASSES = {
    "strict": dict(share=0.30, slack=(0.25, 1.0), priority=(0.2, 0.6),
                   budget=(1.3, 2.2)),
    "batch": dict(share=0.40, slack=(2.0, 8.0), priority=(0.5, 0.8),
                  budget=(1.1, 2.0)),
    "flexible": dict(share=0.30, slack=(8.0, 24.0), priority=(0.7, 1.0),
                     budget=(1.05, 1.9)),
}

MEMORY_GB_PER_CPU = 2

_CACHE = {}


def load_trace():

    if "jobs" not in _CACHE:
        _CACHE["jobs"] = pd.read_csv(TRACE_FILE)

    return _CACHE["jobs"]


def make_trace_workload(
    seed,
    region_names,
    fraction=0.10,
    locality_fraction=0.25,
    gb_per_core_hour=1.0,
    week_offset=True,
):

    rng = np.random.default_rng(seed)

    trace = load_trace().sample(frac=fraction, random_state=seed)

    trace = trace.sort_values("arrival_s")

    offset_h = 168.0 * (seed % 3) if week_offset else 0.0

    n = len(trace)

    names = list(CLASSES)

    classes = rng.choice(
        names, size=n, p=[CLASSES[c]["share"] for c in names]
    )

    homes = rng.choice(list(region_names), size=n)

    pinned = rng.random(n) < locality_fraction

    data_noise = rng.lognormal(0.0, 1.0, size=n)

    uniforms = rng.random((n, 3))

    jobs = []

    for i, row in enumerate(trace.itertuples(index=False)):

        profile = CLASSES[classes[i]]

        runtime = row.runtime_s / 3600.0

        arrival = row.arrival_s / 3600.0 + offset_h

        def draw(bounds, u):
            return bounds[0] + (bounds[1] - bounds[0]) * u

        slack = draw(profile["slack"], uniforms[i, 0])

        cpu = int(row.cpu)

        home = str(homes[i])

        allowed = [home] if pinned[i] else None

        reference_price = REGION_PRICES[home]

        max_cost = (
            cpu * runtime * reference_price
            * draw(profile["budget"], uniforms[i, 1])
        )

        jobs.append(
            Job(
                job_id=f"A{i:06d}",
                arrival_time=arrival,
                cpu_required=cpu,
                memory_required=cpu * MEMORY_GB_PER_CPU,
                runtime=runtime,
                deadline=arrival + runtime + slack,
                flexibility=str(classes[i]),
                max_cost=max_cost,
                carbon_priority=draw(profile["priority"], uniforms[i, 2]),
                allowed_regions=allowed,
                home_region=home,
                data_gb=cpu * runtime * gb_per_core_hour * data_noise[i],
            )
        )

    return jobs
