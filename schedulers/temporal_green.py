import math

from schedulers.base import Scheduler


class TemporalGreenScheduler(Scheduler):
    """
    Carbon-greedy spatio-temporal baseline.

    Strict jobs run now in the greenest available region.
    Deferrable jobs pick the (region, start hour) with the lowest
    FORECAST carbon intensity within `max_wait` hours, as long as
    the deadline can still be met. Cost and SLA risk are ignored,
    the forecast is trusted blindly and the decision is never
    re-evaluated.
    """

    name = "Temporal Green"

    def __init__(self, max_wait=6):
        self.max_wait = max_wait

    def decide(self, job, candidate_regions, current_time):

        available_regions = self.available_regions(
            job,
            candidate_regions
        )

        # --------------------------------
        # Strict workload
        # --------------------------------

        if job.flexibility == "strict":

            if not available_regions:
                return None

            best_region = min(
                available_regions,
                key=lambda region:
                self.current_intensity(region, current_time)
            )

            return best_region

        eligible_regions = self.eligible_regions(
            job,
            candidate_regions
        )

        # --------------------------------
        # Latest time at which the job
        # can start without violating SLA
        # --------------------------------

        latest_start = job.latest_start

        # --------------------------------
        # Search window
        # --------------------------------

        search_until = min(
            current_time + self.max_wait,
            latest_start
        )

        # Deadline can no longer be met:
        # run as soon as possible.
        if search_until < current_time:

            if not available_regions:
                return None

            return min(
                available_regions,
                key=lambda region:
                self.current_intensity(region, current_time)
            )

        # --------------------------------
        # Candidate start times:
        # now + every following full hour
        # --------------------------------

        start_times = [current_time]

        hour = math.floor(current_time) + 1

        while hour <= search_until:
            start_times.append(hour)
            hour += 1

        # --------------------------------
        # Find best region/time
        # --------------------------------

        best_region = None
        best_time = current_time
        best_carbon = float("inf")

        for region in eligible_regions:

            for future_time in start_times:

                # Only "now" requires free capacity now.
                if (
                    future_time == current_time
                    and not region.can_run(job)
                ):
                    continue

                carbon = self.intensity_signal(
                    region,
                    current_time,
                    future_time,
                    job.runtime
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
