from schedulers.base import Scheduler


class GreenestRegionScheduler(Scheduler):
    """
    Greedy spatial-only baseline.

    Always runs immediately in the region with the lowest
    CURRENT carbon intensity. No temporal shifting, no cost
    awareness.
    """

    name = "Greenest Region"

    def decide(self, job, candidate_regions, current_time):

        available_regions = self.available_regions(
            job,
            candidate_regions
        )

        if not available_regions:
            return None

        # Choose the region with the lowest
        # carbon intensity at the current simulation time
        region = min(
            available_regions,
            key=lambda r: self.current_intensity(r, current_time)
        )

        return region
