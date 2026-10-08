"""
Inter-region data-transfer model.

A job's input data lives in its home region. Running it anywhere else
first moves `job.data_gb` gigabytes across the WAN, which costs

    time    data_gb / bandwidth                         (hours)
    energy  data_gb * energy_per_gb                     (kWh)
    carbon  energy * mean(CI_home, CI_target) at start  (gCO2eq)
    money   data_gb * egress_price                      ($)

Defaults
--------
energy_per_gb = 0.005 kWh/GB
    Network energy-intensity estimates have fallen from ~0.06 kWh/GB
    (2015, Aslan et al., J. Industrial Ecology 2018) by roughly half
    every two years; 0.005 kWh/GB is a central 2024 extrapolation. The
    paper sweeps 0.001-0.06 kWh/GB.
egress_price = 0.02 $/GB
    Typical inter-region transfer price of the large public clouds.
bandwidth = 450 GB/h
    ~1 Gbit/s sustained per job.
"""


class NetworkModel:

    def __init__(
        self,
        energy_per_gb=0.005,
        egress_price=0.02,
        bandwidth_gb_per_hour=450.0
    ):

        self.energy_per_gb = energy_per_gb
        self.egress_price = egress_price
        self.bandwidth_gb_per_hour = bandwidth_gb_per_hour

        self.regions = {}

    def bind(self, regions):

        self.regions = {region.name: region for region in regions}

    # ==================================================
    # DOES THE JOB HAVE TO MOVE DATA?
    # ==================================================

    def moves_data(self, job, region):

        return (
            job.home_region is not None
            and job.data_gb > 0
            and region.name != job.home_region
        )

    # ==================================================
    # COMPONENTS
    # ==================================================

    def transfer_hours(self, job, region):

        if not self.moves_data(job, region):
            return 0.0

        return job.data_gb / self.bandwidth_gb_per_hour

    def transfer_energy(self, job, region):

        if not self.moves_data(job, region):
            return 0.0

        return job.data_gb * self.energy_per_gb

    def transfer_cost(self, job, region):

        if not self.moves_data(job, region):
            return 0.0

        return job.data_gb * self.egress_price

    def transfer_intensity(self, job, region, time, intensity_of=None):
        """Mean intensity of the two endpoints (actual by default)."""

        if intensity_of is None:
            intensity_of = lambda r, t: r.get_carbon_intensity(t)

        home = self.regions.get(job.home_region)

        target = intensity_of(region, time)

        if home is None:
            return target

        return 0.5 * (intensity_of(home, time) + target)

    def transfer_carbon(self, job, region, time, intensity_of=None):

        energy = self.transfer_energy(job, region)

        if energy == 0:
            return 0.0

        return energy * self.transfer_intensity(
            job, region, time, intensity_of
        )
