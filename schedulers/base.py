from abc import ABC, abstractmethod


# Sentinel: decide() may return (WAIT, time) to be asked again at `time`
# without committing to a region (used by online threshold policies).
WAIT = object()


class Scheduler(ABC):
    """
    Common interface for every scheduling policy.

    decide(job, candidate_regions, current_time) returns

        None                    nothing can run now (job is queued)
        region                  run immediately in `region`
        (region, start_time)    temporal shift: run at `start_time`
        (WAIT, time)            ask again at `time`

    Hard constraints shared by every policy (so that baselines are
    compared fairly with GreenOps):

        * data locality   (job.allowed_regions)
        * resource fit    (CPU / memory)
        * cost budget     (job.max_cost, including data egress)
    """

    name = "Scheduler"

    # Hours between re-evaluations of a deferred job.
    # None = never re-plan (follow the original decision).
    replan_interval = None

    forecaster = None

    network = None

    # ==================================================
    # SIMULATOR BINDING
    # ==================================================

    def bind(self, regions, forecaster=None, network=None):

        self.forecaster = forecaster

        self.network = network

    # ==================================================
    # DECISION
    # ==================================================

    @abstractmethod
    def decide(self, job, candidate_regions, current_time):
        pass

    # ==================================================
    # DATA-TRANSFER HELPERS
    # ==================================================

    def transfer_hours(self, job, region):

        if self.network is None:
            return 0.0

        return self.network.transfer_hours(job, region)

    def total_cost(self, job, region):
        """Compute cost plus data-egress cost."""

        cost = region.calculate_cost(job)

        if self.network is not None:
            cost += self.network.transfer_cost(job, region)

        return cost

    def latest_start_in(self, job, region):
        """Latest start that still meets the deadline in `region`."""

        return (
            job.deadline
            - job.runtime
            - self.transfer_hours(job, region)
        )

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
                and self.total_cost(job, region) > job.max_cost
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

    def estimated_carbon(self, job, region, current_time, start_time):
        """
        Believed total emissions (gCO2eq) of running `job` in `region`
        from `start_time`: compute energy x forecast intensity over the
        run window, plus the carbon of moving its input data.
        """

        hours = self.transfer_hours(job, region)

        intensity = self.intensity_signal(
            region,
            current_time,
            start_time + hours,
            job.runtime
        )

        if intensity is None:
            return None

        carbon = region.calculate_energy(
            job.runtime,
            job.cpu_required
        ) * intensity

        if self.network is not None:

            carbon += self.network.transfer_carbon(
                job,
                region,
                start_time,
                intensity_of=lambda r, t: self.intensity_signal(
                    r, current_time, t, 0
                ),
            )

        return carbon
