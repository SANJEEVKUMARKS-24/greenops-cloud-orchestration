from schedulers.base import Scheduler


class CostOnlyScheduler(Scheduler):

    def decide(self, job, candidate_regions, current_time):

        available_regions = [
            region
            for region in candidate_regions
            if region.can_run(job)
        ]

        if not available_regions:
            return None

        region = min(
            available_regions,
            key=lambda r: r.cost_per_cpu_hour
        )

        return region