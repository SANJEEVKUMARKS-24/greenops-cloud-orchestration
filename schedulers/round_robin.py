from schedulers.base import Scheduler


class RoundRobinScheduler(Scheduler):
    """
    Carbon-agnostic baseline (Kubernetes-default-like spreading).

    Cycles through the regions that can run the job right now,
    with no regard to carbon, cost or SLA slack.
    """

    name = "Round Robin"

    def __init__(self):
        self.index = 0

    def decide(self, job, candidate_regions, current_time):

        available_regions = self.available_regions(
            job,
            candidate_regions
        )

        if not available_regions:
            return None

        region = available_regions[
            self.index % len(available_regions)
        ]

        self.index += 1

        return region
