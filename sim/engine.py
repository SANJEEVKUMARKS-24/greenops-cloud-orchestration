import simpy


class CloudSimulator:

    def __init__(
        self,
        regions,
        scheduler,
        metrics
    ):

        self.env = simpy.Environment()

        self.regions = regions

        self.scheduler = scheduler

        self.metrics = metrics

    # ==================================================
    # SUBMIT JOB
    # ==================================================

    def submit_job(self, job):

        self.env.process(
            self.process_job(job)
        )

    # ==================================================
    # PROCESS JOB
    # ==================================================

    def process_job(self, job):

        # ==============================================
        # WAIT FOR JOB ARRIVAL
        # ==============================================

        arrival_wait = (
            job.arrival_time
            - self.env.now
        )

        if arrival_wait > 0:

            yield self.env.timeout(
                arrival_wait
            )

        print(
            f"[{self.env.now:.1f}] "
            f"Job {job.job_id} arrived"
        )

        # ==============================================
        # ASK SCHEDULER
        # ==============================================

        decision = self.scheduler.decide(
            job,
            self.regions,
            self.env.now
        )

        # ==============================================
        # NO FEASIBLE DECISION
        # ==============================================

        if decision is None:

            print(
                f"[{self.env.now:.1f}] "
                f"No feasible region for "
                f"{job.job_id}"
            )

            return

        # ==============================================
        # NORMAL SCHEDULER
        #
        # Returns:
        #
        #     region
        #
        # ==============================================

        if not isinstance(
            decision,
            tuple
        ):

            region = decision

            scheduled_time = (
                self.env.now
            )

        # ==============================================
        # TEMPORAL SCHEDULER
        #
        # Returns:
        #
        #     region, scheduled_time
        #
        # ==============================================

        else:

            region, scheduled_time = (
                decision
            )

        # ==============================================
        # WAIT FOR SELECTED EXECUTION TIME
        # ==============================================

        wait_time = (
            scheduled_time
            - self.env.now
        )

        if wait_time > 0:

            print(
                f"[{self.env.now:.1f}] "
                f"Job {job.job_id} waiting "
                f"until "
                f"{scheduled_time:.1f}"
            )

            yield self.env.timeout(
                wait_time
            )

        # ==============================================
        # FINAL RESOURCE CHECK
        # ==============================================

        if not region.can_run(job):

            print(
                f"[{self.env.now:.1f}] "
                f"Region {region.name} "
                f"cannot run "
                f"{job.job_id}"
            )

            return

        # ==============================================
        # FINAL SLA CHECK
        # ==============================================

        if (
            self.env.now
            + job.runtime
            >
            job.deadline
        ):

            job.sla_violated = True

            print(
                f"[{self.env.now:.1f}] "
                f"Job {job.job_id} "
                f"would violate SLA"
            )

            return

        # ==============================================
        # FINAL COST CHECK
        # ==============================================

        estimated_cost = (
            job.cpu_required
            * job.runtime
            * region.cost_per_cpu_hour
        )

        if (
            job.max_cost is not None
            and estimated_cost
            > job.max_cost
        ):

            print(
                f"[{self.env.now:.1f}] "
                f"Job {job.job_id} exceeds "
                f"budget in "
                f"{region.name}"
            )

            return

        # ==============================================
        # ALLOCATE RESOURCES
        # ==============================================

        allocated = region.allocate(
            job
        )

        if not allocated:

            print(
                f"[{self.env.now:.1f}] "
                f"Failed to allocate "
                f"resources for "
                f"{job.job_id}"
            )

            return

        # ==============================================
        # RECORD START
        # ==============================================

        job.assigned_region = (
            region
        )

        job.start_time = (
            self.env.now
        )

        # ==============================================
        # CARBON INTENSITY
        # ==============================================

        carbon_intensity = (
            region.get_carbon_intensity(
                job.start_time
            )
        )

        if carbon_intensity is None:

            print(
                f"ERROR: No carbon data for "
                f"{region.name} at "
                f"hour "
                f"{int(job.start_time) % 24}"
            )

            region.release(job)

            return

        # ==============================================
        # ENERGY CALCULATION
        #
        # NEW MODEL
        #
        # Energy depends on:
        #     Region power characteristics
        #     CPU requirement
        #     Runtime
        # ==============================================

        job.energy_consumed = (
            region.calculate_energy(
                job.runtime,
                job.cpu_required
            )
        )

        # ==============================================
        # CARBON CALCULATION
        # ==============================================

        job.carbon_emitted = (
            job.energy_consumed
            *
            carbon_intensity
        )

        # ==============================================
        # COST
        # ==============================================

        job.cost = (
            estimated_cost
        )

        # ==============================================
        # PRINT EXECUTION INFORMATION
        # ==============================================

        print(
            f"[{self.env.now:.1f}] "
            f"Job {job.job_id} → "
            f"{region.name}"
        )

        print(
            f"           Carbon intensity: "
            f"{carbon_intensity} "
            f"gCO₂/kWh"
        )

        print(
            f"           Energy: "
            f"{job.energy_consumed:.4f} "
            f"kWh"
        )

        print(
            f"           Estimated cost: "
            f"${job.cost:.2f}"
        )

        # ==============================================
        # EXECUTE JOB
        # ==============================================

        yield self.env.timeout(
            job.runtime
        )

        # ==============================================
        # RECORD FINISH
        # ==============================================

        job.finish_time = (
            self.env.now
        )

        # ==============================================
        # SLA VALIDATION
        # ==============================================

        if (
            job.finish_time
            >
            job.deadline
        ):

            job.sla_violated = True

        else:

            job.sla_violated = False

        # ==============================================
        # RELEASE RESOURCES
        # ==============================================

        region.release(
            job
        )

        # ==============================================
        # RECORD METRICS
        # ==============================================

        self.metrics.record(
            job
        )

        # ==============================================
        # COMPLETION MESSAGE
        # ==============================================

        print(
            f"[{self.env.now:.1f}] "
            f"Job {job.job_id} completed "
            f"in {region.name}"
        )

    # ==================================================
    # RUN SIMULATION
    # ==================================================

    def run(self):

        self.env.run()