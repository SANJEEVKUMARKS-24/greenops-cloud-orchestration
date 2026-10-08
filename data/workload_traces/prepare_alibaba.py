"""
Prepare a job-level workload from the Alibaba Cluster Trace v2018.

Source
------
Alibaba Cluster Trace Program, cluster-trace-v2018, batch_task table
(https://github.com/alibaba/clusterdata). 4,000 machines, 8 days,
14.3 M task records.

Columns of batch_task.csv (no header):
    task_name, instance_num, job_name, task_type, status,
    start_time, end_time, plan_cpu, plan_mem

Job-level aggregation
---------------------
* Only tasks with status Terminated and valid start/end times.
* arrival   = earliest task start of the job (submission is not
              recorded; first start is the standard proxy)
* runtime   = latest task end - earliest task start (job makespan)
* cpu       = mean parallelism = sum(instances x plan_cpu/100 x task
              duration) / runtime, rounded up and capped at 64 vCPU
* mem_frac  = largest plan_mem of the job (fraction of a machine)
* Jobs shorter than 5 minutes are dropped: they are 88 % of jobs but
  only 9 % of the CPU-time, and are too short to be worth shifting.

Output: data/workload_traces/alibaba_jobs.csv.gz (~450 k jobs)

Usage:
    python data/workload_traces/prepare_alibaba.py
"""

import os
import tarfile
import urllib.request

import numpy as np
import pandas as pd


HERE = os.path.dirname(os.path.abspath(__file__))

RAW_DIR = os.path.join(HERE, "alibaba_raw")

ARCHIVE = os.path.join(RAW_DIR, "batch_task.tar.gz")

RAW_CSV = os.path.join(RAW_DIR, "batch_task.csv")

OUTPUT = os.path.join(HERE, "alibaba_jobs.csv.gz")

URL = (
    "http://aliopentrace.oss-cn-beijing.aliyuncs.com/"
    "v2018Traces/batch_task.tar.gz"
)

MIN_RUNTIME_S = 300

MAX_CPU = 64


def download():

    os.makedirs(RAW_DIR, exist_ok=True)

    if not os.path.exists(RAW_CSV):

        if not os.path.exists(ARCHIVE):
            print(f"Downloading {URL} (130 MB) ...")
            urllib.request.urlretrieve(URL, ARCHIVE)

        print("Extracting ...")

        with tarfile.open(ARCHIVE) as archive:
            member = archive.getmember("batch_task.csv")
            archive.extract(member, RAW_DIR, filter="data")


def build_jobs():

    columns = ["task", "instances", "job", "type", "status",
               "start", "end", "plan_cpu", "plan_mem"]

    tasks = pd.read_csv(
        RAW_CSV,
        names=columns,
        usecols=["instances", "job", "status", "start", "end",
                 "plan_cpu", "plan_mem"],
        dtype={"instances": "float32", "job": "string",
               "status": "category", "start": "float64", "end": "float64",
               "plan_cpu": "float32", "plan_mem": "float32"},
    )

    print(f"  task records          : {len(tasks):,}")

    tasks = tasks[
        (tasks["status"] == "Terminated")
        & (tasks["start"] > 0)
        & (tasks["end"] > tasks["start"])
        & tasks["plan_cpu"].notna()
    ]

    tasks["core_seconds"] = (
        tasks["instances"] * tasks["plan_cpu"] / 100
        * (tasks["end"] - tasks["start"])
    )

    jobs = tasks.groupby("job").agg(
        start=("start", "min"),
        end=("end", "max"),
        core_seconds=("core_seconds", "sum"),
        mem_frac=("plan_mem", "max"),
    )

    print(f"  terminated jobs       : {len(jobs):,}")

    jobs["runtime_s"] = jobs["end"] - jobs["start"]

    total_core_seconds = jobs["core_seconds"].sum()

    jobs = jobs[jobs["runtime_s"] >= MIN_RUNTIME_S].copy()

    print(
        f"  jobs >= {MIN_RUNTIME_S // 60} min          : {len(jobs):,} "
        f"({jobs['core_seconds'].sum() / total_core_seconds:.1%} "
        f"of CPU-time)"
    )

    jobs["cpu"] = np.minimum(
        np.ceil(jobs["core_seconds"] / jobs["runtime_s"]),
        MAX_CPU,
    ).astype(int).clip(lower=1)

    jobs["arrival_s"] = jobs["start"] - jobs["start"].min()

    jobs["mem_frac"] = jobs["mem_frac"].fillna(0.01).clip(0.001, 1.0)

    out = (
        jobs.reset_index()[["job", "arrival_s", "runtime_s", "cpu",
                            "mem_frac"]]
        .sort_values("arrival_s")
    )

    out.to_csv(OUTPUT, index=False, compression="gzip",
               float_format="%.4f")

    print(f"\n  median runtime        : {out['runtime_s'].median() / 60:.1f} min")
    print(f"  median / p90 vCPU     : {out['cpu'].median():.0f} / "
          f"{out['cpu'].quantile(0.9):.0f}")
    print(f"  span                  : {out['arrival_s'].max() / 3600:.1f} h")
    print(f"\nWritten {OUTPUT}")


if __name__ == "__main__":
    download()
    build_jobs()
