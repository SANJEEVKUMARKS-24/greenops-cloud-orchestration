class Region:

    def __init__(
        self,
        name,
        cpu_capacity,
        memory_capacity,
        cost_per_cpu_hour,
        carbon_trace,
        idle_power_kw=0.10,
        max_power_kw=0.50
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
        # ==========================================

        self.carbon_trace = carbon_trace

        # ==========================================
        # Power model
        #
        # idle_power_kw:
        # Power consumed when the region is idle.
        #
        # max_power_kw:
        # Power consumed at 100% CPU utilization.
        # ==========================================

        self.idle_power_kw = idle_power_kw
        self.max_power_kw = max_power_kw

        # ==========================================
        # Running jobs
        # ==========================================

        self.running_jobs = []

    # ==================================================
    # CARBON INTENSITY
    # ==================================================

    def get_carbon_intensity(self, time):

        hour = int(time) % 24

        return self.carbon_trace.get(hour)

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

        return power

    # ==================================================
    # ENERGY CONSUMPTION
    # ==================================================

    def calculate_energy(
        self,
        runtime,
        cpu_required
    ):

        if runtime <= 0:
            return 0.0

        # ------------------------------------------
        # Calculate utilization caused by job
        # ------------------------------------------

        utilization = (
            cpu_required /
            self.cpu_capacity
        )

        utilization = max(
            0.0,
            min(1.0, utilization)
        )

        # ------------------------------------------
        # Power while job is running
        # ------------------------------------------

        power_kw = (
            self.idle_power_kw
            +
            (
                self.max_power_kw
                -
                self.idle_power_kw
            )
            * utilization
        )

        # ------------------------------------------
        # Energy = Power × Time
        #
        # kWh = kW × hours
        # ------------------------------------------

        energy_kwh = (
            power_kw *
            runtime
        )

        return energy_kwh

    # ==================================================
    # RESOURCE CHECK
    # ==================================================

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
            f"MaxPower={self.max_power_kw}kW"
            f")"
        )