import math

from schedulers.base import Scheduler


class WaitAwhileScheduler(Scheduler):
    """
    Temporal-only baseline after Wiesner et al., "Let's Wait Awhile:
    How Temporal Workload Shifting Can Reduce Carbon Emissions in the
    Cloud" (Middleware '21), non-interruptible strategy.

    * The job never leaves its home region (no spatial shifting).
    * Strict jobs start immediately.
    * Deferrable jobs start at the hour in [now, latest start] (optionally
      capped by `max_wait`) that minimises the FORECAST mean carbon
      intensity over the job's runtime.
    * The decision is taken once at submission (no re-planning).
    """

    name = "Wait Awhile"

    def __init__(self, max_wait=None):
        self.max_wait = max_wait

    def home_region(self, job, candidate_regions):

        eligible = self.eligible_regions(job, candidate_regions)

        for region in eligible:
            if region.name == job.home_region:
                return region

        # Jobs without a home region stay in the first region
        # they are allowed to use.
        return eligible[0] if eligible else None

    def decide(self, job, candidate_regions, current_time):

        home = self.home_region(job, candidate_regions)

        if home is None:
            return None

        if job.flexibility == "strict":
            return home if home.can_run(job) else None

        latest = self.latest_start_in(job, home)

        if self.max_wait is not None:
            latest = min(latest, current_time + self.max_wait)

        start_times = [current_time]

        hour = math.floor(current_time) + 1

        while hour <= latest + 1e-9:
            start_times.append(float(hour))
            hour += 1

        best_time = None
        best_intensity = float("inf")

        for start in start_times:

            if start == current_time and not home.can_run(job):
                continue

            intensity = self.intensity_signal(
                home,
                current_time,
                start,
                job.runtime
            )

            if intensity is not None and intensity < best_intensity:
                best_intensity = intensity
                best_time = start

        if best_time is None:
            return None

        if best_time <= current_time + 1e-9:
            return home

        return home, best_time
