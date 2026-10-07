from schedulers.base import Scheduler


class CostOnlyScheduler(Scheduler):
    """
    Purely economic baseline.

    Always runs immediately in the cheapest region that can
    host the job right now.
    """

    name = "Cost Only"

    def decide(self, job, candidate_regions, current_time):

        available_regions = self.available_regions(
            job,
            candidate_regions
        )

        if not available_regions:
            return None

        region = min(
            available_regions,
            key=lambda r: r.cost_per_cpu_hour
        )

        return region
