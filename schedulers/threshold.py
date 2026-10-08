import math

from schedulers.base import Scheduler, WAIT


class ThresholdScheduler(Scheduler):
    """
    Forecast-free online threshold (reservation-price) baseline.

    Online search with known bounds L <= CI <= U accepts the first
    price below the reservation price  phi = sqrt(L * U), which is
    sqrt(U / L)-competitive (El-Yaniv et al., Algorithmica 2001). This
    threshold rule is the building block of the learning-augmented
    competitive algorithms for spatio-temporal allocation with deadlines
    of Lechowicz et al. (arXiv:2408.07831). This class implements the
    plain (non-learning-augmented, single-shot) variant:

    * Strict jobs run now in the greenest available region.
    * A deferrable job runs as soon as some eligible region with free
      capacity has an EFFECTIVE intensity <= phi, where the effective
      intensity adds the job's data-transfer carbon per kWh of compute
      (movement cost). L and U are the historical bounds of the job's
      eligible regions.
    * Otherwise it waits one hour and checks again; at its latest start
      it runs in the best available region.

    It never uses forecasts, so it is immune to forecast error.
    """

    name = "Online Threshold"

    def bind(self, regions, forecaster=None, network=None):

        super().bind(regions, forecaster, network)

        self.bounds = {}

        for region in regions:

            values = [v for v in region._hourly if v is not None and v > 0]

            self.bounds[region.name] = (min(values), max(values))

    def effective_intensity(self, job, region, current_time):

        intensity = self.current_intensity(region, current_time)

        if self.network is None:
            return intensity

        energy = region.calculate_energy(job.runtime, job.cpu_required)

        if energy <= 0:
            return intensity

        transfer = self.network.transfer_carbon(job, region, current_time)

        return intensity + transfer / energy

    def threshold(self, eligible):

        low = min(self.bounds[r.name][0] for r in eligible)
        high = max(self.bounds[r.name][1] for r in eligible)

        return math.sqrt(low * high)

    def decide(self, job, candidate_regions, current_time):

        eligible = self.eligible_regions(job, candidate_regions)

        if not eligible:
            return None

        available = [r for r in eligible if r.can_run(job)]

        best = min(
            available,
            key=lambda r: self.effective_intensity(job, r, current_time),
            default=None,
        )

        if job.flexibility == "strict":
            return best

        if (
            best is not None
            and self.effective_intensity(job, best, current_time)
            <= self.threshold(eligible)
        ):
            return best

        latest = max(self.latest_start_in(job, r) for r in eligible)

        if current_time >= latest - 1e-9:
            return best

        return WAIT, min(math.floor(current_time) + 1.0, latest)
