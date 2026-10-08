from schedulers.base import Scheduler


class CostOnlyScheduler(Scheduler):
    """
    Purely economic baseline.

    Always runs immediately in the region with the lowest total
    cost (compute + data egress) that can host the job right now.
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
            key=lambda r: self.total_cost(job, r)
        )

        return region
