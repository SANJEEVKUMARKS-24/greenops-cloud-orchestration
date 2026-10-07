from abc import ABC, abstractmethod


class Scheduler(ABC):
    """
    Common interface for every scheduling policy.

    decide(job, candidate_regions, current_time) returns

        None                    nothing can run now (job is queued)
        region                  run immediately in `region`
        (region, start_time)    temporal shift: run at `start_time`

    Hard constraints shared by every policy (so that baselines are
    compared fairly with GreenOps):

        * data locality   (job.allowed_regions)
        * resource fit    (CPU / memory)
        * cost budget     (job.max_cost)
    """

    name = "Scheduler"

    # Hours between re-evaluations of a deferred job.
    # None = never re-plan (follow the original decision).
    replan_interval = None

    forecaster = None

    # ==================================================
    # SIMULATOR BINDING
    # ==================================================

    def bind(self, regions, forecaster=None):

        self.forecaster = forecaster

    # ==================================================
    # DECISION
    # ==================================================

    @abstractmethod
    def decide(self, job, candidate_regions, current_time):
        pass

    # ==================================================
    # FEASIBILITY HELPERS
    # ==================================================

    def eligible_regions(self, job, candidate_regions):
        """Regions that could host the job at SOME time."""

        eligible = []

        for region in candidate_regions:

            if not job.is_allowed_in(region):
                continue

            if not region.fits(job):
                continue

            if (
                job.max_cost is not None
                and region.calculate_cost(job) > job.max_cost
            ):
                continue

            eligible.append(region)

        return eligible

    def available_regions(self, job, candidate_regions):
        """Eligible regions with free capacity RIGHT NOW."""

        return [
            region
            for region in self.eligible_regions(
                job,
                candidate_regions
            )
            if region.can_run(job)
        ]

    # ==================================================
    # CARBON SIGNAL
    #
    # What the scheduler BELIEVES the intensity will be
    # over [start_time, start_time + duration].
    #
    # With a forecaster attached the future is uncertain;
    # without one the scheduler has perfect information.
    # ==================================================

    def intensity_signal(
        self,
        region,
        current_time,
        start_time,
        duration
    ):

        if self.forecaster is not None:

            return self.forecaster.forecast_average(
                region,
                current_time,
                start_time,
                duration
            )

        return region.average_carbon_intensity(
            start_time,
            duration
        )

    def current_intensity(self, region, current_time):
        """Real-time (measured) intensity - no forecast error."""

        return region.get_carbon_intensity(current_time)
