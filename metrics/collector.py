import pandas as pd


class MetricsCollector:

    def __init__(self):
        self.results = []

    # ==================================================
    # RECORD ONE JOB (completed or rejected)
    # ==================================================

    def record(self, job):

        completed = job.status == "completed"

        latency = (
            job.finish_time - job.arrival_time
            if completed else None
        )

        result = {
            "job_id": job.job_id,
            "flexibility": job.flexibility,
            "status": job.status or "completed",
            "region": (
                job.assigned_region.name
                if job.assigned_region else None
            ),
            "arrival_time": job.arrival_time,
            "start_time": job.start_time,
            "finish_time": job.finish_time,
            "runtime": job.runtime,
            "deadline": job.deadline,
            "cpu_required": job.cpu_required,
            "waiting_time": (
                job.start_time - job.arrival_time
                if completed else None
            ),
            "latency": latency,
            "sla_violated": bool(job.sla_violated) if completed else True,
            "tardiness": job.tardiness if completed else None,
            "energy_consumed": job.energy_consumed,
            "carbon_intensity": job.carbon_intensity,
            "carbon_emitted": job.carbon_emitted,
            "cost": job.cost,
            "decisions": job.decisions,
        }

        self.results.append(result)

    def get_results(self):
        return self.results

    def dataframe(self):
        return pd.DataFrame(self.results)

    # ==================================================
    # SUMMARY
    # ==================================================

    def summary(self):

        df = pd.DataFrame(self.results)

        if df.empty:
            return {}

        done = df[df["status"] == "completed"]

        summary = {
            "total_jobs": len(df),
            "completed_jobs": len(done),
            "rejected_jobs": int((df["status"] == "rejected").sum()),
            "total_carbon_g": done["carbon_emitted"].sum(),
            "total_energy_kwh": done["energy_consumed"].sum(),
            "total_cost": done["cost"].sum(),
            "avg_carbon_intensity": (
                done["carbon_emitted"].sum()
                / done["energy_consumed"].sum()
                if done["energy_consumed"].sum() > 0 else 0.0
            ),
            # Violations among completed jobs (deadline missed).
            "sla_violations": int(done["sla_violated"].sum()),
            "sla_violation_rate": (
                done["sla_violated"].mean() * 100
                if len(done) else 0.0
            ),
            "mean_tardiness": (
                done["tardiness"].mean() if len(done) else 0.0
            ),
            "max_tardiness": (
                done["tardiness"].max() if len(done) else 0.0
            ),
            "average_latency": done["latency"].mean(),
            "p95_latency": done["latency"].quantile(0.95),
            "p99_latency": done["latency"].quantile(0.99),
            "average_wait": done["waiting_time"].mean(),
        }

        # ----------------------------------------------
        # Per workload class
        # ----------------------------------------------

        for flexibility, group in done.groupby("flexibility"):

            summary[f"{flexibility}_sla_violations"] = int(
                group["sla_violated"].sum()
            )

            summary[f"{flexibility}_avg_latency"] = (
                group["latency"].mean()
            )

            summary[f"{flexibility}_carbon_g"] = (
                group["carbon_emitted"].sum()
            )

        # ----------------------------------------------
        # Where did the work go? (share of CPU-hours)
        # ----------------------------------------------

        cpu_hours = done["cpu_required"] * done["runtime"]

        total_cpu_hours = cpu_hours.sum()

        for region, share in cpu_hours.groupby(done["region"]).sum().items():

            summary[f"share_{region}"] = (
                share / total_cpu_hours * 100
                if total_cpu_hours else 0.0
            )

        return summary

    def save_csv(self, filename):

        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
