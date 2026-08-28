from schedulers.base import Scheduler


class TemporalGreenScheduler(Scheduler):

    def __init__(self, max_wait=6):
        self.max_wait = max_wait

    def decide(self, job, candidate_regions, current_time):

        available_regions = [
            region
            for region in candidate_regions
            if region.can_run(job)
        ]

        if not available_regions:
            return None

        # --------------------------------
        # Strict workload
        # --------------------------------

        if job.flexibility == "strict":

            best_region = min(
                available_regions,
                key=lambda region:
                region.get_carbon_intensity(current_time)
            )

            return best_region

        # --------------------------------
        # Latest time at which the job
        # can start without violating SLA
        # --------------------------------

        latest_start = job.deadline - job.runtime

        # --------------------------------
        # Search window
        # --------------------------------

        search_until = min(
            current_time + self.max_wait,
            latest_start
        )

        if search_until < current_time:
            return None

        # --------------------------------
        # Find best region/time
        # --------------------------------

        best_region = None
        best_time = current_time
        best_carbon = float("inf")

        for region in available_regions:

            for future_time in range(
                int(current_time),
                int(search_until) + 1
            ):

                # Make sure the job finishes
                # before its deadline.
                if future_time + job.runtime > job.deadline:
                    continue

                carbon = region.get_carbon_intensity(
                    future_time
                )

                if carbon is None:
                    continue

                if carbon < best_carbon:

                    best_carbon = carbon
                    best_region = region
                    best_time = future_time

        if best_region is None:
            return None

        return best_region, best_time