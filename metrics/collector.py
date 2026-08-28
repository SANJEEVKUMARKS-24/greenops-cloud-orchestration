import pandas as pd


class MetricsCollector:

    def __init__(self):
        self.results = []

    def record(self, job):

        latency = job.finish_time - job.arrival_time

        result = {
            "job_id": job.job_id,
            "region": job.assigned_region.name,
            "arrival_time": job.arrival_time,
            "start_time": job.start_time,
            "finish_time": job.finish_time,
            "runtime": job.runtime,
            "deadline": job.deadline,
            "latency": latency,
            "sla_violated": job.sla_violated,
            "energy_consumed": job.energy_consumed,
            "carbon_emitted": job.carbon_emitted,
            "cost": job.cost
        }

        self.results.append(result)

    def get_results(self):
        return self.results

    def summary(self):

        df = pd.DataFrame(self.results)

        if df.empty:
            return {}

        return {
            "total_jobs": len(df),
            "completed_jobs": len(df),
            "total_carbon_g": df["carbon_emitted"].sum(),
            "total_energy_kwh": df["energy_consumed"].sum(),
            "total_cost": df["cost"].sum(),
            "sla_violations": df["sla_violated"].sum(),
            "sla_violation_rate": (
                df["sla_violated"].mean() * 100
            ),
            "average_latency": df["latency"].mean(),
            "p95_latency": df["latency"].quantile(0.95)
        }

    def save_csv(self, filename):

        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)