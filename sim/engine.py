import simpy

from schedulers.base import WAIT


class CloudSimulator:
    """
    Discrete-event simulation of a multi-region cloud.

    Life cycle of a job
    -------------------
    1. ARRIVAL      the job enters the system at `arrival_time`.
    2. ADMISSION    if no region can EVER host it (locality, size or
                    budget) it is rejected and recorded.
    3. DECISION     the scheduler returns either
                        region                     -> run now
                        (region, start_time)       -> temporal shift
                        (WAIT, time)               -> re-decide at time
                        None                       -> nothing free now
    4. QUEUEING     if nothing is free the job waits for the next
                    resource release (or `retry_interval`) and asks
                    again - jobs are never silently dropped.
    5. DEFERRAL     a temporally shifted job sleeps until its start
                    time. Schedulers with `replan_interval` are
                    re-consulted every interval with a fresher
                    forecast ("wait vs run now" re-evaluation).
    6. EXECUTION    resources are allocated; energy, carbon (averaged
                    over the whole run window using the ACTUAL trace)
                    and cost are computed; resources are released.
    7. METRICS      completion, latency and SLA tardiness are recorded.
    """

    def __init__(
        self,
        regions,
        scheduler,
        metrics,
        forecaster=None,
        network=None,
        verbose=True,
        retry_interval=0.25
    ):

        self.env = simpy.Environment()

        self.regions = regions

        self.scheduler = scheduler

        self.metrics = metrics

        self.forecaster = forecaster

        self.network = network

        if network is not None:
            network.bind(regions)

        self.verbose = verbose

        self.retry_interval = retry_interval

        self._release_event = self.env.event()

        if hasattr(self.scheduler, "bind"):
            self.scheduler.bind(regions, forecaster, network)

    # ==================================================
    # LOGGING
    # ==================================================

    def log(self, message):

        if self.verbose:
            print(f"[{self.env.now:6.2f}] {message}")

    # ==================================================
    # SUBMIT JOB
    # ==================================================

    def submit_job(self, job):

        self.env.process(
            self.process_job(job)
        )

    # ==================================================
    # RESOURCE RELEASE NOTIFICATION
    # ==================================================

    def _notify_release(self):

        event = self._release_event

        self._release_event = self.env.event()

        event.succeed()

    def _wait_for_resources(self):

        return (
            self._release_event
            | self.env.timeout(self.retry_interval)
        )

    # ==================================================
    # COST INCLUDING DATA EGRESS
    # ==================================================

    def _total_cost(self, job, region):

        cost = region.calculate_cost(job)

        if self.network is not None:
            cost += self.network.transfer_cost(job, region)

        return cost

    # ==================================================
    # ADMISSION CONTROL
    # ==================================================

    def _admissible(self, job):

        for region in self.regions:

            if not job.is_allowed_in(region):
                continue

            if not region.fits(job):
                continue

            if (
                job.max_cost is not None
                and self._total_cost(job, region) > job.max_cost
            ):
                continue

            return True

        return False

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

        self.log(f"Job {job.job_id} arrived ({job.flexibility})")

        # ==============================================
        # ADMISSION
        # ==============================================

        if not self._admissible(job):

            job.status = "rejected"
            job.reject_reason = "no region satisfies locality/size/budget"

            self.log(f"Job {job.job_id} REJECTED: {job.reject_reason}")

            self.metrics.record(job)

            return

        # ==============================================
        # DECISION LOOP
        # ==============================================

        while True:

            decision = self.scheduler.decide(
                job,
                self.regions,
                self.env.now
            )

            job.decisions += 1

            # ------------------------------------------
            # Nothing free right now -> queue
            # ------------------------------------------

            if decision is None:

                self.log(f"Job {job.job_id} queued (no capacity)")

                yield self._wait_for_resources()

                continue

            # ------------------------------------------
            # Explicit "wait and ask me again"
            # ------------------------------------------

            if isinstance(decision, tuple) and decision[0] is WAIT:

                yield self.env.timeout(
                    max(decision[1] - self.env.now, 1e-6)
                )

                continue

            # ------------------------------------------
            # NORMAL SCHEDULER returns: region
            # TEMPORAL SCHEDULER returns: region, time
            # ------------------------------------------

            if isinstance(decision, tuple):

                region, scheduled_time = decision

            else:

                region = decision

                scheduled_time = self.env.now

            # ------------------------------------------
            # Temporal shift
            # ------------------------------------------

            wait_time = scheduled_time - self.env.now

            if wait_time > 1e-9:

                replan = getattr(
                    self.scheduler,
                    "replan_interval",
                    None
                )

                if replan and wait_time > replan:

                    self.log(
                        f"Job {job.job_id} deferred towards "
                        f"{region.name} @ {scheduled_time:.1f} "
                        f"(re-plan in {replan}h)"
                    )

                    yield self.env.timeout(replan)

                    continue

                self.log(
                    f"Job {job.job_id} waiting until "
                    f"{scheduled_time:.1f} for {region.name}"
                )

                yield self.env.timeout(wait_time)

            # ------------------------------------------
            # Capacity may have been taken while waiting
            # ------------------------------------------

            if region.can_run(job):
                break

            self.log(
                f"Region {region.name} cannot run {job.job_id} "
                f"now - re-deciding"
            )

            if wait_time <= 1e-9:

                yield self._wait_for_resources()

        # ==============================================
        # ALLOCATE RESOURCES
        # ==============================================

        region.allocate(job)

        job.assigned_region = region

        job.start_time = self.env.now

        # ==============================================
        # ENERGY, CARBON AND COST
        #
        # Carbon uses the ACTUAL intensity averaged over
        # the whole execution window - not the forecast
        # the scheduler used to make its decision.
        # ==============================================

        # ----------------------------------------------
        # Data transfer (only outside the home region).
        # Resources are held while the input is staged.
        # ----------------------------------------------

        if self.network is not None:

            job.transfer_hours = self.network.transfer_hours(job, region)
            job.transfer_energy = self.network.transfer_energy(job, region)
            job.transfer_carbon = self.network.transfer_carbon(
                job, region, job.start_time
            )
            job.transfer_cost = self.network.transfer_cost(job, region)

        compute_start = job.start_time + job.transfer_hours

        job.energy_consumed = region.calculate_energy(
            job.runtime,
            job.cpu_required
        )

        job.carbon_intensity = region.average_carbon_intensity(
            compute_start,
            job.runtime
        )

        job.carbon_emitted = (
            job.energy_consumed
            * job.carbon_intensity
            + job.transfer_carbon
        )

        job.cost = region.calculate_cost(job) + job.transfer_cost

        self.log(
            f"Job {job.job_id} -> {region.name}  "
            f"CI={job.carbon_intensity:.1f} gCO2/kWh  "
            f"E={job.energy_consumed:.3f} kWh  "
            f"C={job.carbon_emitted:.1f} g  "
            f"${job.cost:.2f}"
        )

        # ==============================================
        # EXECUTE JOB
        # ==============================================

        yield self.env.timeout(
            job.transfer_hours + job.runtime
        )

        # ==============================================
        # RECORD FINISH + SLA VALIDATION
        # ==============================================

        job.finish_time = self.env.now

        job.sla_violated = (
            job.finish_time > job.deadline + 1e-9
        )

        job.status = "completed"

        region.release(job)

        self._notify_release()

        self.metrics.record(job)

        self.log(
            f"Job {job.job_id} completed in {region.name}"
            + ("  ** SLA VIOLATED **" if job.sla_violated else "")
        )

    # ==================================================
    # RUN SIMULATION
    # ==================================================

    def run(self, until=None):

        self.env.run(until=until)
