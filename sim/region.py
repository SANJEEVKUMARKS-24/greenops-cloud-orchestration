import math


class Region:

    def __init__(
        self,
        name,
        cpu_capacity,
        memory_capacity,
        cost_per_cpu_hour,
        carbon_trace,
        idle_power_kw=0.10,
        max_power_kw=0.50,
        pue=1.0,
        node_cpus=None
    ):

        # ==========================================
        # Basic region information
        # ==========================================

        self.name = name

        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity

        self.available_cpu = cpu_capacity
        self.available_memory = memory_capacity

        # ==========================================
        # Economic information
        # ==========================================

        self.cost_per_cpu_hour = (
            cost_per_cpu_hour
        )

        # ==========================================
        # Carbon information
        #
        # Two trace formats are supported:
        #
        #   dict {hour_of_day: intensity}
        #       Controlled 24-hour profile that repeats
        #       every day (used by the 5-job experiment).
        #
        #   list [intensity_h0, intensity_h1, ...]
        #       Historical hourly trace covering several
        #       weeks. Time t uses index floor(t) and wraps
        #       around at the end of the trace.
        # ==========================================

        if isinstance(carbon_trace, dict):

            self.carbon_trace = carbon_trace

            self._hourly = [
                carbon_trace.get(hour)
                for hour in range(24)
            ]

        else:

            self.carbon_trace = list(carbon_trace)

            self._hourly = self.carbon_trace

        # ==========================================
        # Power model
        #
        # idle_power_kw:
        # Power consumed when the region is idle.
        #
        # max_power_kw:
        # Power consumed at 100% CPU utilization.
        #
        # pue:
        # Power Usage Effectiveness of the facility
        # (cooling, power distribution overhead).
        # ==========================================

        self.idle_power_kw = idle_power_kw
        self.max_power_kw = max_power_kw

        self.pue = pue

        # idle/max power are specified for one node of
        # `node_cpus` vCPUs; a region is a pool of such nodes.
        # Default: the whole region is one node.
        self.node_cpus = node_cpus or cpu_capacity

        # ==========================================
        # Running jobs
        # ==========================================

        self.running_jobs = []

    # ==================================================
    # CARBON INTENSITY
    # ==================================================

    @property
    def trace_length(self):

        return len(self._hourly)

    def get_carbon_intensity(self, time):

        index = int(math.floor(time)) % self.trace_length

        return self._hourly[index]

    def average_carbon_intensity(
        self,
        start_time,
        duration
    ):
        """
        Time-weighted average intensity over
        [start_time, start_time + duration].

        A job that runs for several hours is exposed to
        every hourly value it overlaps, not only to the
        value at its start time.
        """

        if duration <= 0:
            return self.get_carbon_intensity(start_time)

        end_time = start_time + duration

        total = 0.0

        t = start_time

        while t < end_time - 1e-9:

            next_boundary = min(
                math.floor(t) + 1,
                end_time
            )

            intensity = self.get_carbon_intensity(t)

            if intensity is None:
                return None

            total += intensity * (next_boundary - t)

            t = next_boundary

        return total / duration

    # ==================================================
    # CPU UTILIZATION
    # ==================================================

    def get_cpu_utilization(self):

        if self.cpu_capacity <= 0:
            return 0.0

        used_cpu = (
            self.cpu_capacity
            - self.available_cpu
        )

        utilization = (
            used_cpu /
            self.cpu_capacity
        )

        # Keep value between 0 and 1
        return max(
            0.0,
            min(1.0, utilization)
        )

    # ==================================================
    # POWER CONSUMPTION
    # ==================================================

    def get_power_consumption(self):

        utilization = (
            self.get_cpu_utilization()
        )

        power = (
            self.idle_power_kw
            +
            (
                self.max_power_kw
                -
                self.idle_power_kw
            )
            * utilization
        )

        return power * self.pue

    # ==================================================
    # ENERGY CONSUMPTION
    # ==================================================

    def calculate_energy(
        self,
        runtime,
        cpu_required
    ):
        """
        Facility energy (kWh) attributed to one job.

        The job's CPU share of a node is

            share = cpu_required / node_cpus

        (a job wider than one node spans several nodes, share > 1)

        It is charged its share of the dynamic power AND
        its share of the idle (static) power, so that the
        energy of jobs running side by side adds up to the
        region's real power draw instead of counting the
        idle power once per job:

            P_job = share * idle + share * (max - idle)
                  = share * max

        and the facility overhead is applied through PUE.
        """

        if runtime <= 0:
            return 0.0

        # ------------------------------------------
        # Calculate utilization caused by job
        # ------------------------------------------

        share = max(
            0.0,
            cpu_required / self.node_cpus
        )

        # ------------------------------------------
        # Power while job is running
        # ------------------------------------------

        power_kw = (
            share * self.idle_power_kw
            +
            share
            * (
                self.max_power_kw
                -
                self.idle_power_kw
            )
        )

        # ------------------------------------------
        # Energy = Power × Time × PUE
        #
        # kWh = kW × hours
        # ------------------------------------------

        energy_kwh = (
            power_kw *
            runtime *
            self.pue
        )

        return energy_kwh

    # ==================================================
    # COST
    # ==================================================

    def calculate_cost(self, job):

        return (
            job.cpu_required
            * job.runtime
            * self.cost_per_cpu_hour
        )

    # ==================================================
    # RESOURCE CHECK
    # ==================================================

    def fits(self, job):
        """Could the job EVER fit in this region?"""

        return (
            job.cpu_required <= self.cpu_capacity
            and job.memory_required <= self.memory_capacity
        )

    def can_run(self, job):

        return (
            self.available_cpu >=
            job.cpu_required
            and
            self.available_memory >=
            job.memory_required
        )

    # ==================================================
    # ALLOCATE RESOURCES
    # ==================================================

    def allocate(self, job):

        if not self.can_run(job):
            return False

        self.available_cpu -= (
            job.cpu_required
        )

        self.available_memory -= (
            job.memory_required
        )

        self.running_jobs.append(job)

        return True

    # ==================================================
    # RELEASE RESOURCES
    # ==================================================

    def release(self, job):

        self.available_cpu += (
            job.cpu_required
        )

        self.available_memory += (
            job.memory_required
        )

        if job in self.running_jobs:

            self.running_jobs.remove(job)

    # ==================================================
    # REPRESENTATION
    # ==================================================

    def __repr__(self):

        return (
            f"Region("
            f"name={self.name}, "
            f"CPU={self.available_cpu}/"
            f"{self.cpu_capacity}, "
            f"Memory={self.available_memory}/"
            f"{self.memory_capacity}, "
            f"IdlePower={self.idle_power_kw}kW, "
            f"MaxPower={self.max_power_kw}kW, "
            f"PUE={self.pue}"
            f")"
        )
