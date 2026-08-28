from schedulers.base import Scheduler


class CarbonAwareMOOScheduler(Scheduler):

    def __init__(
        self,
        carbon_weight=0.5,
        cost_weight=0.2,
        waiting_weight=0.3,
        max_wait=6
    ):
        self.carbon_weight = carbon_weight
        self.cost_weight = cost_weight
        self.waiting_weight = waiting_weight
        self.max_wait = max_wait

    # ==================================================
    # ENERGY MODEL
    # ==================================================

    def calculate_energy(self, job):

        return (
            job.cpu_required *
            job.runtime
        )

    # ==================================================
    # COST MODEL
    # ==================================================

    def calculate_cost(self, job, region):

        return (
            job.cpu_required *
            job.runtime *
            region.cost_per_cpu_hour
        )

    # ==================================================
    # CARBON MODEL
    # ==================================================

    def calculate_carbon(
        self,
        job,
        region,
        start_time
    ):

        carbon_intensity = (
            region.get_carbon_intensity(start_time)
        )

        if carbon_intensity is None:
            return None

        energy = self.calculate_energy(job)

        return (
            energy *
            carbon_intensity
        )

    # ==================================================
    # MIN-MAX NORMALIZATION
    # ==================================================

    def normalize(
        self,
        value,
        minimum,
        maximum
    ):

        if maximum == minimum:
            return 0.0

        return (
            (value - minimum) /
            (maximum - minimum)
        )

    # ==================================================
    # CREATE FEASIBLE CANDIDATES
    # ==================================================

    def generate_candidates(
        self,
        job,
        candidate_regions,
        current_time
    ):

        candidates = []

        # ----------------------------------------------
        # Latest possible start time
        # ----------------------------------------------

        latest_start = (
            job.deadline -
            job.runtime
        )

        # ----------------------------------------------
        # Search window
        # ----------------------------------------------

        search_until = min(
            current_time + self.max_wait,
            latest_start
        )

        if search_until < current_time:
            return candidates

        # ----------------------------------------------
        # Evaluate every region
        # ----------------------------------------------

        for region in candidate_regions:

            # ------------------------------------------
            # Resource constraint
            # ------------------------------------------

            if not region.can_run(job):
                continue

            # ------------------------------------------
            # Cost
            # ------------------------------------------

            cost = self.calculate_cost(
                job,
                region
            )

            # ------------------------------------------
            # HARD BUDGET CONSTRAINT
            # ------------------------------------------

            if (
                job.max_cost is not None
                and cost > job.max_cost
            ):
                continue

            # ------------------------------------------
            # Evaluate possible start times
            # ------------------------------------------

            for start_time in range(
                int(current_time),
                int(search_until) + 1
            ):

                finish_time = (
                    start_time +
                    job.runtime
                )

                # --------------------------------------
                # HARD SLA CONSTRAINT
                # --------------------------------------

                if finish_time > job.deadline:
                    continue

                carbon = self.calculate_carbon(
                    job,
                    region,
                    start_time
                )

                if carbon is None:
                    continue

                waiting_time = (
                    start_time -
                    current_time
                )

                remaining_slack = (
                    job.deadline -
                    finish_time
                )

                candidates.append(
                    {
                        "region": region,
                        "start_time": start_time,
                        "finish_time": finish_time,
                        "carbon": carbon,
                        "cost": cost,
                        "waiting_time": waiting_time,
                        "remaining_slack": remaining_slack
                    }
                )

        return candidates

    # ==================================================
    # SCORE CANDIDATES
    # ==================================================

    def score_candidates(
        self,
        candidates,
        job
    ):

        if not candidates:
            return []

        # ----------------------------------------------
        # Extract objective values
        # ----------------------------------------------

        carbon_values = [
            candidate["carbon"]
            for candidate in candidates
        ]

        cost_values = [
            candidate["cost"]
            for candidate in candidates
        ]

        waiting_values = [
            candidate["waiting_time"]
            for candidate in candidates
        ]

        # ----------------------------------------------
        # Min/max values
        # ----------------------------------------------

        carbon_min = min(carbon_values)
        carbon_max = max(carbon_values)

        cost_min = min(cost_values)
        cost_max = max(cost_values)

        waiting_min = min(waiting_values)
        waiting_max = max(waiting_values)

        # ----------------------------------------------
        # Normalize and calculate score
        # ----------------------------------------------

        for candidate in candidates:

            carbon_normalized = self.normalize(
                candidate["carbon"],
                carbon_min,
                carbon_max
            )

            cost_normalized = self.normalize(
                candidate["cost"],
                cost_min,
                cost_max
            )

            waiting_normalized = self.normalize(
                candidate["waiting_time"],
                waiting_min,
                waiting_max
            )

            # ------------------------------------------
            # Carbon priority of this workload
            # ------------------------------------------

            carbon_factor = job.carbon_priority

            # ------------------------------------------
            # Final multi-objective score
            #
            # Lower is better.
            # ------------------------------------------

            score = (

                self.carbon_weight *
                carbon_factor *
                carbon_normalized

                +

                self.cost_weight *
                cost_normalized

                +

                self.waiting_weight *
                waiting_normalized
            )

            candidate["carbon_normalized"] = (
                carbon_normalized
            )

            candidate["cost_normalized"] = (
                cost_normalized
            )

            candidate["waiting_normalized"] = (
                waiting_normalized
            )

            candidate["score"] = score

        return candidates

    # ==================================================
    # DECISION FUNCTION
    # ==================================================

    def decide(
        self,
        job,
        candidate_regions,
        current_time
    ):

        # ==================================================
        # STRICT JOB
        # ==================================================

        if job.flexibility == "strict":

            candidates = []

            for region in candidate_regions:

                if not region.can_run(job):
                    continue

                cost = self.calculate_cost(
                    job,
                    region
                )

                # Budget constraint
                if (
                    job.max_cost is not None
                    and cost > job.max_cost
                ):
                    continue

                carbon = self.calculate_carbon(
                    job,
                    region,
                    current_time
                )

                if carbon is None:
                    continue

                candidates.append(
                    {
                        "region": region,
                        "carbon": carbon,
                        "cost": cost,
                        "start_time": current_time
                    }
                )

            if not candidates:
                return None

            # Strict jobs run immediately.
            # Among feasible regions choose
            # the lowest-carbon region.

            best = min(
                candidates,
                key=lambda candidate:
                candidate["carbon"]
            )

            print(
                f"    Decision: {job.job_id} "
                f"is STRICT → "
                f"{best['region'].name}"
            )

            return best["region"]

        # ==================================================
        # FLEXIBLE / BATCH JOB
        # ==================================================

        candidates = self.generate_candidates(
            job,
            candidate_regions,
            current_time
        )

        if not candidates:
            return None

        # ----------------------------------------------
        # Score all feasible candidates
        # ----------------------------------------------

        candidates = self.score_candidates(
            candidates,
            job
        )

        # ----------------------------------------------
        # Select lowest score
        # ----------------------------------------------

        best = min(
            candidates,
            key=lambda candidate:
            candidate["score"]
        )

        # ==================================================
        # PRINT DECISION
        # ==================================================

        print(
            f"    Decision: {job.job_id} → "
            f"{best['region'].name} "
            f"@ {best['start_time']}"
        )

        print(
            f"        Carbon: "
            f"{best['carbon']:.2f} gCO₂"
        )

        print(
            f"        Cost: "
            f"${best['cost']:.2f}"
        )

        print(
            f"        Waiting: "
            f"{best['waiting_time']:.1f} hours"
        )

        print(
            f"        Remaining SLA slack: "
            f"{best['remaining_slack']:.1f} hours"
        )

        print(
            f"        Normalized carbon: "
            f"{best['carbon_normalized']:.4f}"
        )

        print(
            f"        Normalized cost: "
            f"{best['cost_normalized']:.4f}"
        )

        print(
            f"        Normalized waiting: "
            f"{best['waiting_normalized']:.4f}"
        )

        print(
            f"        Final score: "
            f"{best['score']:.6f}"
        )

        # ==================================================
        # RETURN REGION + EXECUTION TIME
        # ==================================================

        return (
            best["region"],
            best["start_time"]
        )