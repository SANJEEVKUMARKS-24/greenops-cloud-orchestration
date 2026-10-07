import math

from schedulers.base import Scheduler


class CarbonAwareMOOScheduler(Scheduler):
    """
    GreenOps Multi-Objective Carbon-Aware Scheduler.

    Decision variables
        x = (region r, start time s)

    Hard constraints (never traded off)
        locality      r in job.allowed_regions
        capacity      r can host the job (now, if s = now)
        budget        cost(r) <= job.max_cost
        SLA           s + runtime <= deadline
        strict jobs   s = now  (no temporal shifting)

    Objectives (all minimised)
        C(x)  forecast carbon  = E_r * CI_forecast(r, s..s+runtime)
              risk-adjusted    * (1 + kappa * sigma(s - now))
        K(x)  cost             = cpu * runtime * price_r
        R(x)  SLA risk         = ((s - now) / (latest_start - now)) ** q
              = fraction of the remaining slack consumed by waiting,
              made convex (q = 2) so that waiting is cheap while
              plenty of slack remains and expensive near the deadline

    Selection
        mode="weighted"  weighted sum (Option A)
            score = w_c * p_job * C/Cmax + w_k * K/Kmax + w_r * R
        mode="pareto"    Pareto filter + weighted Tchebycheff knee
            (Option B) - can select points on non-convex parts of
            the front that a weighted sum can never reach.

    Temporal shifting is forecast-aware and confidence-gated:
    the carbon estimate of a deferred candidate is inflated by the
    forecast uncertainty of its horizon (kappa * sigma), so the
    scheduler only waits when the expected saving is larger than
    the forecast can be wrong. Deferred jobs are re-planned every
    `replan_interval` hours with a fresher (more accurate) forecast.
    """

    name = "GreenOps MOO"

    def __init__(
        self,
        carbon_weight=0.5,
        cost_weight=0.2,
        waiting_weight=0.3,
        max_wait=6,
        mode="weighted",
        risk_aversion=0.5,
        replan_interval=1.0,
        normalization="max",
        risk_exponent=2.0,
        verbose=False
    ):
        self.carbon_weight = carbon_weight
        self.cost_weight = cost_weight
        self.waiting_weight = waiting_weight
        self.max_wait = max_wait

        if mode not in ("weighted", "pareto"):
            raise ValueError(f"unknown mode {mode!r}")

        if normalization not in ("max", "minmax"):
            raise ValueError(f"unknown normalization {normalization!r}")

        self.mode = mode
        self.risk_aversion = risk_aversion
        self.replan_interval = replan_interval
        self.normalization = normalization
        self.risk_exponent = risk_exponent
        self.verbose = verbose

    # ==================================================
    # ENERGY MODEL
    #
    # Same model the simulator uses to charge the job.
    # ==================================================

    def calculate_energy(self, job, region):

        return region.calculate_energy(
            job.runtime,
            job.cpu_required
        )

    # ==================================================
    # COST MODEL
    # ==================================================

    def calculate_cost(self, job, region):

        return region.calculate_cost(job)

    # ==================================================
    # CARBON MODEL
    # ==================================================

    def calculate_carbon(
        self,
        job,
        region,
        start_time,
        current_time=None
    ):

        if current_time is None:
            current_time = start_time

        carbon_intensity = self.intensity_signal(
            region,
            current_time,
            start_time,
            job.runtime
        )

        if carbon_intensity is None:
            return None

        energy = self.calculate_energy(job, region)

        return (
            energy *
            carbon_intensity
        )

    def forecast_sigma(self, horizon):

        if self.forecaster is None:
            return 0.0

        return self.forecaster.sigma(horizon)

    # ==================================================
    # NORMALIZATION
    # ==================================================

    def normalize(
        self,
        value,
        minimum,
        maximum
    ):

        if self.normalization == "minmax":

            if maximum == minimum:
                return 0.0

            return (
                (value - minimum) /
                (maximum - minimum)
            )

        # Ratio-to-max keeps relative magnitudes: a 2 g
        # difference between 300 g and 302 g is not blown
        # up into the full [0, 1] range.
        if maximum <= 0:
            return 0.0

        return value / maximum

    # ==================================================
    # CANDIDATE START TIMES
    # ==================================================

    def start_times(self, job, current_time):

        if job.flexibility == "strict":
            return [current_time]

        search_until = min(
            current_time + self.max_wait,
            job.latest_start
        )

        times = [current_time]

        hour = math.floor(current_time) + 1

        while hour <= search_until + 1e-9:
            times.append(float(hour))
            hour += 1

        return times

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
        # Remaining slack at decision time
        # ----------------------------------------------

        remaining_slack = job.latest_start - current_time

        start_times = self.start_times(
            job,
            current_time
        )

        # ----------------------------------------------
        # Spatial dimension: every eligible region
        # (locality + size + budget already enforced)
        # ----------------------------------------------

        for region in self.eligible_regions(
            job,
            candidate_regions
        ):

            cost = self.calculate_cost(
                job,
                region
            )

            # ------------------------------------------
            # Temporal dimension: every start time
            # ------------------------------------------

            for start_time in start_times:

                waiting_time = start_time - current_time

                # Capacity is only known for "now".
                # Future slots are re-checked when the
                # job wakes up.
                if (
                    waiting_time <= 1e-9
                    and not region.can_run(job)
                ):
                    continue

                finish_time = start_time + job.runtime

                # --------------------------------------
                # HARD SLA CONSTRAINT
                # (a job already past its latest start
                #  may only run now - best effort)
                # --------------------------------------

                if (
                    waiting_time > 1e-9
                    and finish_time > job.deadline + 1e-9
                ):
                    continue

                carbon = self.calculate_carbon(
                    job,
                    region,
                    start_time,
                    current_time
                )

                if carbon is None:
                    continue

                sigma = self.forecast_sigma(waiting_time)

                carbon_adjusted = carbon * (
                    1 + self.risk_aversion * sigma
                )

                if remaining_slack > 1e-9:
                    sla_risk = min(
                        1.0,
                        waiting_time / remaining_slack
                    ) ** self.risk_exponent
                else:
                    sla_risk = 0.0

                candidates.append(
                    {
                        "region": region,
                        "start_time": start_time,
                        "finish_time": finish_time,
                        "carbon": carbon,
                        "carbon_adjusted": carbon_adjusted,
                        "cost": cost,
                        "waiting_time": waiting_time,
                        "sla_risk": sla_risk,
                        "remaining_slack": job.deadline - finish_time
                    }
                )

        return candidates

    # ==================================================
    # SCORE CANDIDATES (weighted sum)
    # ==================================================

    def score_candidates(
        self,
        candidates,
        job
    ):

        if not candidates:
            return []

        carbon_values = [c["carbon_adjusted"] for c in candidates]
        cost_values = [c["cost"] for c in candidates]

        carbon_min, carbon_max = min(carbon_values), max(carbon_values)
        cost_min, cost_max = min(cost_values), max(cost_values)

        # ------------------------------------------
        # Carbon priority of this workload
        # ------------------------------------------

        carbon_factor = job.carbon_priority

        for candidate in candidates:

            carbon_normalized = self.normalize(
                candidate["carbon_adjusted"],
                carbon_min,
                carbon_max
            )

            cost_normalized = self.normalize(
                candidate["cost"],
                cost_min,
                cost_max
            )

            # SLA risk is already a fraction in [0, 1]
            waiting_normalized = candidate["sla_risk"]

            # ------------------------------------------
            # Final multi-objective score
            #
            # Lower is better.
            # ------------------------------------------

            score = (
                self.carbon_weight
                * carbon_factor
                * carbon_normalized
                + self.cost_weight
                * cost_normalized
                + self.waiting_weight
                * waiting_normalized
            )

            candidate["carbon_normalized"] = carbon_normalized
            candidate["cost_normalized"] = cost_normalized
            candidate["waiting_normalized"] = waiting_normalized
            candidate["score"] = score

        return candidates

    # ==================================================
    # PARETO FRONT
    # ==================================================

    @staticmethod
    def objectives(candidate):

        return (
            candidate["carbon_adjusted"],
            candidate["cost"],
            candidate["sla_risk"]
        )

    @classmethod
    def dominates(cls, a, b):

        fa = cls.objectives(a)
        fb = cls.objectives(b)

        return (
            all(x <= y for x, y in zip(fa, fb))
            and any(x < y for x, y in zip(fa, fb))
        )

    @classmethod
    def pareto_front(cls, candidates):

        return [
            c
            for c in candidates
            if not any(
                cls.dominates(other, c)
                for other in candidates
                if other is not c
            )
        ]

    def select_knee(self, front, job):
        """
        Weighted Tchebycheff selection on the Pareto front:

            argmin_x  max_i  w_i * (f_i(x) - f_i*) / (f_i^N - f_i*)

        with ideal point f* and nadir point f^N of the front.
        """

        weights = (
            self.carbon_weight * job.carbon_priority,
            self.cost_weight,
            self.waiting_weight
        )

        values = [self.objectives(c) for c in front]

        ideal = [min(v[i] for v in values) for i in range(3)]
        nadir = [max(v[i] for v in values) for i in range(3)]

        def tchebycheff(candidate):

            f = self.objectives(candidate)

            terms = []

            for i in range(3):

                span = nadir[i] - ideal[i]

                normalized = (
                    0.0 if span <= 0
                    else (f[i] - ideal[i]) / span
                )

                terms.append(weights[i] * normalized)

            # Tie-break on the weighted sum.
            return (max(terms), sum(terms))

        for candidate in front:
            candidate["score"] = tchebycheff(candidate)[0]

        return min(front, key=tchebycheff)

    # ==================================================
    # DECISION FUNCTION
    # ==================================================

    def decide(
        self,
        job,
        candidate_regions,
        current_time
    ):

        candidates = self.generate_candidates(
            job,
            candidate_regions,
            current_time
        )

        if not candidates:
            return None

        if self.mode == "pareto":

            front = self.pareto_front(candidates)

            best = self.select_knee(front, job)

        else:

            candidates = self.score_candidates(
                candidates,
                job
            )

            # Ties are broken in favour of running earlier.
            best = min(
                candidates,
                key=lambda c: (c["score"], c["waiting_time"])
            )

        # ==================================================
        # PRINT DECISION
        # ==================================================

        if self.verbose:

            print(
                f"    Decision: {job.job_id} ({job.flexibility}) -> "
                f"{best['region'].name} @ {best['start_time']:.1f}  "
                f"carbon={best['carbon']:.1f} g  "
                f"cost=${best['cost']:.2f}  "
                f"wait={best['waiting_time']:.1f} h  "
                f"slack left={best['remaining_slack']:.1f} h  "
                f"score={best['score']:.4f}  "
                f"({len(candidates)} candidates)"
            )

        # ==================================================
        # RETURN REGION + EXECUTION TIME
        # ==================================================

        if best["waiting_time"] <= 1e-9:
            return best["region"]

        return (
            best["region"],
            best["start_time"]
        )
