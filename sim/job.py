class Job:

    def __init__(
        self,
        job_id,
        arrival_time,
        cpu_required,
        memory_required,
        runtime,
        deadline,
        flexibility="strict",
        max_cost=None,
        carbon_priority=0.5,
        allowed_regions=None,
        home_region=None,
        data_gb=0.0
    ):

        self.job_id = job_id

        self.arrival_time = arrival_time

        self.cpu_required = cpu_required
        self.memory_required = memory_required

        self.runtime = runtime
        self.deadline = deadline

        # strict | batch | flexible
        self.flexibility = flexibility

        # Maximum amount the customer is willing
        # to spend on this workload.
        #
        # None = no explicit budget constraint.
        self.max_cost = max_cost

        # Carbon preference:
        #
        # 0.0 = no carbon preference
        # 1.0 = maximum carbon priority
        self.carbon_priority = carbon_priority

        # Data-locality / data-sovereignty constraint.
        #
        # None = the job may run in any region.
        # Otherwise a collection of region names.
        self.allowed_regions = (
            None
            if not allowed_regions
            else frozenset(allowed_regions)
        )

        # Region where the job's input data lives and how
        # much of it must be moved if the job runs elsewhere.
        self.home_region = home_region
        self.data_gb = data_gb

        # --------------------------------
        # Scheduling information
        # --------------------------------

        self.start_time = None
        self.finish_time = None
        self.assigned_region = None

        # completed | rejected
        self.status = None
        self.reject_reason = None

        # How many times the scheduler was consulted
        # (initial decision + re-planning + retries).
        self.decisions = 0

        # --------------------------------
        # Metrics
        # --------------------------------

        self.sla_violated = False

        self.energy_consumed = 0
        self.carbon_emitted = 0
        self.carbon_intensity = 0
        self.cost = 0

        self.transfer_hours = 0.0
        self.transfer_energy = 0.0
        self.transfer_carbon = 0.0
        self.transfer_cost = 0.0

    # ==================================================
    # DERIVED PROPERTIES
    # ==================================================

    @property
    def latest_start(self):

        return self.deadline - self.runtime

    @property
    def slack(self):
        """Total scheduling slack at arrival (hours)."""

        return max(
            0.0,
            self.deadline
            - self.arrival_time
            - self.runtime
        )

    @property
    def tardiness(self):

        if self.finish_time is None:
            return 0.0

        return max(
            0.0,
            self.finish_time - self.deadline
        )

    def is_allowed_in(self, region):

        return (
            self.allowed_regions is None
            or region.name in self.allowed_regions
        )

    def __repr__(self):

        return (
            f"Job("
            f"id={self.job_id}, "
            f"arrival={self.arrival_time}, "
            f"runtime={self.runtime}, "
            f"deadline={self.deadline}, "
            f"flexibility={self.flexibility}, "
            f"max_cost={self.max_cost}, "
            f"carbon_priority={self.carbon_priority}"
            f")"
        )
