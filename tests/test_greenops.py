"""
Unit and integration tests for the GreenOps simulator and schedulers.

Run with:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sim.job import Job
from sim.region import Region
from sim.engine import CloudSimulator
from sim.forecast import CarbonForecaster

from metrics.collector import MetricsCollector

from schedulers.round_robin import RoundRobinScheduler
from schedulers.cost_only import CostOnlyScheduler
from schedulers.greenest_region import GreenestRegionScheduler
from schedulers.temporal_green import TemporalGreenScheduler
from schedulers.carbon_aware_moo import CarbonAwareMOOScheduler

from experiments.evaluation import hypervolume_2d, paired_permutation_test


# ============================================================
# HELPERS
# ============================================================

def flat(value, hours=48):
    return [value] * hours


def dip(high, low, dip_start, dip_end, hours=48):
    """High intensity except for a clean window [dip_start, dip_end)."""
    return [
        low if dip_start <= h < dip_end else high
        for h in range(hours)
    ]


def region(name, trace, cost=0.10, cpu=16, memory=32):
    return Region(
        name=name,
        cpu_capacity=cpu,
        memory_capacity=memory,
        cost_per_cpu_hour=cost,
        carbon_trace=trace,
    )


def job(job_id="J1", arrival=0, cpu=2, runtime=2, deadline=10,
        flexibility="flexible", max_cost=None, priority=0.8,
        allowed=None):
    return Job(
        job_id=job_id,
        arrival_time=arrival,
        cpu_required=cpu,
        memory_required=2,
        runtime=runtime,
        deadline=deadline,
        flexibility=flexibility,
        max_cost=max_cost,
        carbon_priority=priority,
        allowed_regions=allowed,
    )


def simulate(scheduler, regions, jobs, forecaster=None):
    metrics = MetricsCollector()
    sim = CloudSimulator(regions, scheduler, metrics,
                         forecaster=forecaster, verbose=False)
    for j in jobs:
        sim.submit_job(j)
    sim.run()
    return metrics


# ============================================================
# REGION
# ============================================================

class RegionTests(unittest.TestCase):

    def test_controlled_trace_repeats_daily(self):
        r = region("R", {h: h * 10 for h in range(24)})
        self.assertEqual(r.get_carbon_intensity(5.7), 50)
        self.assertEqual(r.get_carbon_intensity(29), 50)

    def test_historical_trace_indexing_and_wrap(self):
        r = region("R", list(range(100, 148)))
        self.assertEqual(r.get_carbon_intensity(0), 100)
        self.assertEqual(r.get_carbon_intensity(47.9), 147)
        self.assertEqual(r.get_carbon_intensity(48), 100)

    def test_average_intensity_is_time_weighted(self):
        r = region("R", [100, 200, 300, 400])
        self.assertAlmostEqual(r.average_carbon_intensity(0, 2), 150)
        # 0.5 h @ 100 + 1 h @ 200 + 0.5 h @ 300
        self.assertAlmostEqual(r.average_carbon_intensity(0.5, 2), 200)

    def test_energy_of_colocated_jobs_adds_up_to_region_power(self):
        r = Region("R", 16, 32, 0.1, flat(100),
                   idle_power_kw=0.1, max_power_kw=0.5, pue=1.0)
        # Two half-region jobs must not exceed full-load power.
        total = r.calculate_energy(1, 8) + r.calculate_energy(1, 8)
        self.assertAlmostEqual(total, 0.5)

    def test_pue_scales_energy(self):
        a = Region("A", 16, 32, 0.1, flat(100), pue=1.0)
        b = Region("B", 16, 32, 0.1, flat(100), pue=1.5)
        self.assertAlmostEqual(
            b.calculate_energy(2, 4), 1.5 * a.calculate_energy(2, 4)
        )

    def test_allocate_release(self):
        r = region("R", flat(100), cpu=4)
        j = job(cpu=4)
        self.assertTrue(r.allocate(j))
        self.assertFalse(r.can_run(job(cpu=1)))
        r.release(j)
        self.assertEqual(r.available_cpu, 4)


# ============================================================
# FORECASTER
# ============================================================

class ForecasterTests(unittest.TestCase):

    def test_zero_error_is_oracle(self):
        r = region("R", list(range(100, 148)))
        f = CarbonForecaster([r], error_level=0.0)
        self.assertEqual(f.forecast(r, 0, 10), r.get_carbon_intensity(10))

    def test_current_hour_is_exact(self):
        r = region("R", list(range(100, 148)))
        f = CarbonForecaster([r], error_level=0.5, seed=3)
        self.assertEqual(f.forecast(r, 10.4, 10.9), 110)

    def test_error_shrinks_as_target_approaches(self):
        r = region("R", flat(200, 200))
        f = CarbonForecaster([r], error_level=0.3, seed=1)
        far = abs(f.forecast(r, 0, 30) - 200)
        near = abs(f.forecast(r, 29, 30) - 200)
        self.assertLessEqual(near, far)

    def test_deterministic_for_seed(self):
        r = region("R", flat(200, 200))
        a = CarbonForecaster([r], error_level=0.2, seed=5)
        b = CarbonForecaster([r], error_level=0.2, seed=5)
        self.assertEqual(a.forecast(r, 0, 20), b.forecast(r, 0, 20))


# ============================================================
# MOO SCHEDULER - HARD CONSTRAINTS
# ============================================================

class MOOConstraintTests(unittest.TestCase):

    def test_zero_slack_job_is_never_deferred(self):
        r = region("R", dip(500, 50, 3, 10))
        j = job(runtime=4, deadline=4)  # slack = 0
        decision = CarbonAwareMOOScheduler(max_wait=24).decide(j, [r], 0)
        self.assertIs(decision, r)

    def test_strict_job_runs_now(self):
        r = region("R", dip(500, 50, 2, 10))
        j = job(flexibility="strict", deadline=20)
        decision = CarbonAwareMOOScheduler(max_wait=24).decide(j, [r], 0)
        self.assertIs(decision, r)

    def test_large_slack_job_waits_for_clean_window(self):
        r = region("R", dip(600, 60, 6, 12))
        j = job(runtime=2, deadline=40, priority=1.0)
        decision = CarbonAwareMOOScheduler(max_wait=24).decide(j, [r], 0)
        self.assertIsInstance(decision, tuple)
        self.assertEqual(decision[1], 6)

    def test_deferral_never_breaks_deadline(self):
        r = region("R", dip(600, 10, 8, 20))
        j = job(runtime=3, deadline=9, priority=1.0)  # latest start 6
        decision = CarbonAwareMOOScheduler(max_wait=24).decide(j, [r], 0)
        start = decision[1] if isinstance(decision, tuple) else 0
        self.assertLessEqual(start + j.runtime, j.deadline)

    def test_budget_is_respected(self):
        cheap = region("Cheap", flat(700), cost=0.05)
        green = region("Green", flat(20), cost=1.00)
        j = job(cpu=2, runtime=2, max_cost=1.0)  # Green costs 4.0
        decision = CarbonAwareMOOScheduler().decide(j, [cheap, green], 0)
        chosen = decision[0] if isinstance(decision, tuple) else decision
        self.assertIs(chosen, cheap)

    def test_locality_is_respected(self):
        dirty = region("Dirty", flat(700))
        green = region("Green", flat(20))
        j = job(allowed=["Dirty"])
        for scheduler in (CarbonAwareMOOScheduler(), GreenestRegionScheduler(),
                          TemporalGreenScheduler(), CostOnlyScheduler(),
                          RoundRobinScheduler()):
            decision = scheduler.decide(j, [dirty, green], 0)
            chosen = decision[0] if isinstance(decision, tuple) else decision
            self.assertIs(chosen, dirty, scheduler.name)

    def test_spatial_shift_to_green_region(self):
        dirty = region("Dirty", flat(700), cost=0.10)
        green = region("Green", flat(30), cost=0.12)
        j = job(flexibility="strict", priority=0.8)
        self.assertIs(
            CarbonAwareMOOScheduler().decide(j, [dirty, green], 0), green
        )

    def test_cost_weight_can_override_small_carbon_gain(self):
        a = region("A", flat(300), cost=0.05)
        b = region("B", flat(290), cost=0.20)
        j = job(flexibility="strict", priority=0.5)
        self.assertIs(CarbonAwareMOOScheduler().decide(j, [a, b], 0), a)

    def test_no_capacity_returns_none(self):
        r = region("R", flat(100), cpu=2)
        r.allocate(job("X", cpu=2))
        self.assertIsNone(
            CarbonAwareMOOScheduler().decide(job(flexibility="strict"), [r], 0)
        )

    def test_confidence_gate_reduces_deferral_under_uncertainty(self):
        # Waiting saves only 8 % - less than the forecast can be wrong.
        r = region("R", dip(100, 92, 10, 14, hours=72))
        j = job(runtime=2, deadline=60, priority=1.0)
        f = CarbonForecaster([r], error_level=0.5, seed=0)
        gated = CarbonAwareMOOScheduler(max_wait=24, risk_aversion=2.0)
        gated.bind([r], f)
        self.assertIs(gated.decide(j, [r], 0), r)


# ============================================================
# PARETO MODE
# ============================================================

class ParetoTests(unittest.TestCase):

    def test_pareto_front_removes_dominated(self):
        cands = [
            dict(carbon_adjusted=1, cost=1, sla_risk=0),
            dict(carbon_adjusted=2, cost=2, sla_risk=0),   # dominated
            dict(carbon_adjusted=0.5, cost=3, sla_risk=0),
        ]
        front = CarbonAwareMOOScheduler.pareto_front(cands)
        self.assertEqual(len(front), 2)
        self.assertNotIn(cands[1], front)

    def test_pareto_decision_is_on_front(self):
        regions = [region("A", flat(700), 0.05), region("B", flat(30), 0.2),
                   region("C", flat(300), 0.1)]
        s = CarbonAwareMOOScheduler(mode="pareto")
        j = job()
        cands = s.generate_candidates(j, regions, 0)
        decision = s.decide(j, regions, 0)
        chosen = decision[0] if isinstance(decision, tuple) else decision
        front_regions = {c["region"] for c in s.pareto_front(cands)}
        self.assertIn(chosen, front_regions)


# ============================================================
# ENGINE (INTEGRATION)
# ============================================================

class EngineTests(unittest.TestCase):

    def test_jobs_are_queued_not_dropped(self):
        r = region("R", flat(100), cpu=4)
        jobs = [job(f"J{i}", cpu=4, runtime=1, deadline=20,
                    flexibility="strict") for i in range(3)]
        m = simulate(RoundRobinScheduler(), [r], jobs)
        s = m.summary()
        self.assertEqual(s["completed_jobs"], 3)
        starts = sorted(x["start_time"] for x in m.get_results())
        self.assertEqual(starts, [0, 1, 2])

    def test_late_job_is_recorded_as_violation_with_tardiness(self):
        r = region("R", flat(100), cpu=4)
        jobs = [job("A", cpu=4, runtime=3, deadline=3, flexibility="strict"),
                job("B", cpu=4, runtime=2, deadline=2, flexibility="strict")]
        m = simulate(RoundRobinScheduler(), [r], jobs)
        b = next(x for x in m.get_results() if x["job_id"] == "B")
        self.assertTrue(b["sla_violated"])
        self.assertAlmostEqual(b["tardiness"], 3)

    def test_unaffordable_job_is_rejected_and_counted(self):
        r = region("R", flat(100), cost=1.0)
        m = simulate(GreenestRegionScheduler(), [r],
                     [job(cpu=2, runtime=2, max_cost=0.5)])
        s = m.summary()
        self.assertEqual(s["rejected_jobs"], 1)
        self.assertEqual(s["completed_jobs"], 0)

    def test_carbon_uses_whole_run_window(self):
        r = region("R", [100, 300] + flat(300, 46))
        r.pue = 1.0
        j = job(flexibility="strict", runtime=2, cpu=16)
        m = simulate(GreenestRegionScheduler(), [r], [j])
        res = m.get_results()[0]
        self.assertAlmostEqual(res["carbon_intensity"], 200)
        self.assertAlmostEqual(res["carbon_emitted"],
                               res["energy_consumed"] * 200)

    def test_temporal_shift_reduces_carbon_end_to_end(self):
        trace = dip(600, 60, 6, 12)
        j1 = job(runtime=2, deadline=40, priority=1.0)
        j2 = job(runtime=2, deadline=40, priority=1.0)
        greedy = simulate(GreenestRegionScheduler(), [region("R", trace)], [j1])
        moo = simulate(CarbonAwareMOOScheduler(max_wait=24),
                       [region("R", trace)], [j2])
        self.assertLess(moo.summary()["total_carbon_g"],
                        greedy.summary()["total_carbon_g"] / 5)
        self.assertEqual(moo.summary()["sla_violations"], 0)

    def test_moo_never_violates_sla_with_spare_capacity(self):
        trace = dip(600, 60, 6, 12, hours=200)
        jobs = [job(f"J{i}", arrival=i, runtime=2, deadline=i + 2 + (i % 7),
                    flexibility=("strict", "batch", "flexible")[i % 3])
                for i in range(60)]
        m = simulate(CarbonAwareMOOScheduler(max_wait=24),
                     [region("R", trace, cpu=64)], jobs)
        self.assertEqual(m.summary()["sla_violations"], 0)
        self.assertEqual(m.summary()["completed_jobs"], 60)

    def test_replanning_with_noisy_forecast_still_meets_deadline(self):
        trace = dip(500, 100, 10, 16, hours=72)
        r = region("R", trace)
        f = CarbonForecaster([r], error_level=0.5, seed=2)
        j = job(runtime=2, deadline=20, priority=1.0)
        m = simulate(CarbonAwareMOOScheduler(max_wait=24), [r], [j],
                     forecaster=f)
        res = m.get_results()[0]
        self.assertFalse(res["sla_violated"])
        self.assertGreater(res["decisions"], 1)


# ============================================================
# EVALUATION UTILITIES
# ============================================================

class StatisticsTests(unittest.TestCase):

    def test_hypervolume_single_point(self):
        self.assertAlmostEqual(hypervolume_2d([(0, 0)], (1, 1)), 1.0)

    def test_hypervolume_two_points(self):
        # union of [0.2,1]x[0.6,1] and [0.6,1]x[0.2,1]
        hv = hypervolume_2d([(0.2, 0.6), (0.6, 0.2)], (1, 1))
        self.assertAlmostEqual(hv, 0.32 + 0.32 - 0.16)

    def test_hypervolume_ignores_dominated(self):
        a = hypervolume_2d([(0.2, 0.2)], (1, 1))
        b = hypervolume_2d([(0.2, 0.2), (0.5, 0.5)], (1, 1))
        self.assertAlmostEqual(a, b)

    def test_permutation_test_detects_clear_difference(self):
        _, p = paired_permutation_test([10] * 20, [12] * 20)
        self.assertLess(p, 0.001)

    def test_permutation_test_no_difference(self):
        _, p = paired_permutation_test([1, 2, 3, 4], [2, 1, 4, 3])
        self.assertGreater(p, 0.5)


if __name__ == "__main__":
    unittest.main()
