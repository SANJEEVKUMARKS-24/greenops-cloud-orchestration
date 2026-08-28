from schedulers.base import Scheduler


class RoundRobinScheduler(Scheduler):

    def __init__(self):
        self.index = 0

    def decide(self, job, candidate_regions, current_time):

        available_regions = [
            region
            for region in candidate_regions
            if region.can_run(job)
        ]

        if not available_regions:
            return None

        region = available_regions[
            self.index % len(available_regions)
        ]

        self.index += 1

        return region