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
        carbon_priority=0.5
    ):

        self.job_id = job_id

        self.arrival_time = arrival_time

        self.cpu_required = cpu_required
        self.memory_required = memory_required

        self.runtime = runtime
        self.deadline = deadline

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

        # --------------------------------
        # Scheduling information
        # --------------------------------

        self.start_time = None
        self.finish_time = None
        self.assigned_region = None

        # --------------------------------
        # Metrics
        # --------------------------------

        self.sla_violated = False

        self.energy_consumed = 0
        self.carbon_emitted = 0
        self.cost = 0

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