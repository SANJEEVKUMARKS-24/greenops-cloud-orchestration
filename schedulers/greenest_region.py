from schedulers.base import Scheduler


class GreenestRegionScheduler(Scheduler):

    def decide(self, job, candidate_regions, current_time):

        available_regions = [
            region
            for region in candidate_regions
            if region.can_run(job)
        ]

        if not available_regions:
            return None

        # Choose the region with the lowest
        # carbon intensity at the current simulation time
        region = min(
            available_regions,
            key=lambda r: r.get_carbon_intensity(current_time)
        )

        return region