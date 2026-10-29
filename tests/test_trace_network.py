"""
Tests for the data-transfer model, the published-algorithm baselines and
the trace-driven workload.
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
from sim.network import NetworkModel

from schedulers.base import WAIT
from schedulers.carbon_aware_moo import CarbonAwareMOOScheduler
from schedulers.wait_awhile import WaitAwhileScheduler
from schedulers.threshold import ThresholdScheduler

from tests.test_greenops import dip, flat, simulate


def region(name, trace, cost=0.10, cpu=64):
    return Region(name, cpu, 4 * cpu, cost, trace, idle_power_kw=0.1,
                  max_power_kw=0.5, pue=1.0, node_cpus=16)


def job(job_id="J", arrival=0, cpu=16, runtime=2, deadline=30,
        flexibility="flexible", home=None, data_gb=0.0, allowed=None,
        max_cost=None, priority=1.0):
    return Job(job_id, arrival, cpu, cpu, runtime, deadline, flexibility,
               max_cost, priority, allowed_regions=allowed,
               home_region=home, data_gb=data_gb)


# ============================================================
# NETWORK MODEL
# ============================================================

class NetworkTests(unittest.TestCase):

    def setUp(self):
        self.home = region("Home", flat(400))
        self.away = region("Away", flat(100))
        self.net = NetworkModel(energy_per_gb=0.01, egress_price=0.02,
                                bandwidth_gb_per_hour=100)
        self.net.bind([self.home, self.away])

    def test_no_transfer_at_home(self):
        j = job(home="Home", data_gb=50)
        self.assertEqual(self.net.transfer_hours(j, self.home), 0)
        self.assertEqual(self.net.transfer_carbon(j, self.home, 0), 0)

    def test_transfer_components(self):
        j = job(home="Home", data_gb=50)
        self.assertAlmostEqual(self.net.transfer_hours(j, self.away), 0.5)
        self.assertAlmostEqual(self.net.transfer_energy(j, self.away), 0.5)
        self.assertAlmostEqual(self.net.transfer_cost(j, self.away), 1.0)
        # mean of endpoint intensities (400 + 100) / 2
        self.assertAlmostEqual(
            self.net.transfer_carbon(j, self.away, 0), 0.5 * 250
        )

    def test_engine_charges_transfer(self):
        j = job(home="Home", data_gb=50, flexibility="strict")
        net = NetworkModel(energy_per_gb=0.01, bandwidth_gb_per_hour=100)
        from schedulers.greenest_region import GreenestRegionScheduler
        m = simulate_with_network(GreenestRegionScheduler(),
                                  [region("Home", flat(400)),
                                   region("Away", flat(100))], [j], net)
        res = m.get_results()[0]
        self.assertEqual(res["region"], "Away")
        self.assertTrue(res["moved"])
        self.assertAlmostEqual(res["transfer_carbon"], 125)
        self.assertAlmostEqual(res["start_time"], 0.5)
        self.assertAlmostEqual(res["finish_time"], 2.5)

    def test_transfer_does_not_hold_cpus(self):
        from schedulers.round_robin import RoundRobinScheduler
        net = NetworkModel(bandwidth_gb_per_hour=10)
        away = region("Away", flat(100), cpu=16)
        home = region("Home", flat(100), cpu=16)
        # Mover stages 50 GB (5 h) into Away; a local job in Away
        # must be able to use the full region meanwhile.
        mover = job("M", cpu=16, runtime=1, deadline=50, flexibility="strict",
                    home="Home", data_gb=50, allowed=["Away"])
        local = job("L", arrival=1, cpu=16, runtime=2, deadline=10,
                    flexibility="strict", home="Away", allowed=["Away"])
        m = simulate_with_network(RoundRobinScheduler(), [away, home],
                                  [mover, local], net)
        res = {r["job_id"]: r for r in m.get_results()}
        self.assertAlmostEqual(res["L"]["start_time"], 1.0)
        self.assertAlmostEqual(res["M"]["start_time"], 5.0)


def simulate_with_network(scheduler, regions, jobs, network):
    from metrics.collector import MetricsCollector
    from sim.engine import CloudSimulator
    metrics = MetricsCollector()
    sim = CloudSimulator(regions, scheduler, metrics, network=network,
                         verbose=False)
    for j in jobs:
        sim.submit_job(j)
    sim.run()
    return metrics


# ============================================================
# GREENOPS IS DATA-AWARE
# ============================================================

class DataAwareMOOTests(unittest.TestCase):

    def test_huge_dataset_stays_home(self):
        home = region("Home", flat(300))
        away = region("Away", flat(250))
        net = NetworkModel(energy_per_gb=0.05)
        net.bind([home, away])
        s = CarbonAwareMOOScheduler()
        s.bind([home, away], None, net)
        j = job(home="Home", data_gb=5000, flexibility="strict")
        self.assertIs(s.decide(j, [home, away], 0), home)

    def test_small_dataset_moves_to_clean_region(self):
        home = region("Home", flat(700))
        away = region("Away", flat(30))
        net = NetworkModel()
        net.bind([home, away])
        s = CarbonAwareMOOScheduler()
        s.bind([home, away], None, net)
        j = job(home="Home", data_gb=1, flexibility="strict")
        self.assertIs(s.decide(j, [home, away], 0), away)

    def test_transfer_time_counts_against_deadline(self):
        home = region("Home", flat(700))
        away = region("Away", flat(30))
        net = NetworkModel(bandwidth_gb_per_hour=10)
        net.bind([home, away])
        s = CarbonAwareMOOScheduler()
        s.bind([home, away], None, net)
        # 50 GB takes 5 h to move; deadline leaves only 1 h of slack.
        j = job(home="Home", data_gb=50, runtime=2, deadline=3,
                flexibility="batch")
        decision = s.decide(j, [home, away], 0)
        chosen = decision[0] if isinstance(decision, tuple) else decision
        self.assertIs(chosen, home)


# ============================================================
# WAIT AWHILE (Wiesner et al.)
# ============================================================

class WaitAwhileTests(unittest.TestCase):

    def test_never_leaves_home(self):
        home = region("Home", flat(700))
        away = region("Away", flat(10))
        j = job(home="Home")
        d = WaitAwhileScheduler().decide(j, [home, away], 0)
        chosen = d[0] if isinstance(d, tuple) else d
        self.assertIs(chosen, home)

    def test_picks_cleanest_window_before_deadline(self):
        home = region("Home", dip(600, 50, 8, 12))
        j = job(home="Home", runtime=2, deadline=30)
        self.assertEqual(WaitAwhileScheduler().decide(j, [home], 0),
                         (home, 8.0))

    def test_uses_full_slack(self):
        home = region("Home", dip(600, 50, 20, 24))
        j = job(home="Home", runtime=2, deadline=30)
        self.assertEqual(WaitAwhileScheduler().decide(j, [home], 0)[1], 20.0)


# ============================================================
# ONLINE THRESHOLD
# ============================================================

class ThresholdTests(unittest.TestCase):

    def make(self, trace):
        r = region("R", trace)
        s = ThresholdScheduler()
        s.bind([r])
        return r, s

    def test_runs_when_below_reservation_price(self):
        # bounds 100..400 -> phi = 200
        r, s = self.make([150] + [100] * 10 + [400] * 37)
        self.assertIs(s.decide(job(), [r], 0), r)

    def test_waits_when_above_reservation_price(self):
        r, s = self.make([300] * 5 + [100] + [400] * 42)
        decision = s.decide(job(), [r], 0)
        self.assertIs(decision[0], WAIT)
        self.assertEqual(decision[1], 1.0)

    def test_runs_at_latest_start(self):
        r, s = self.make([300] * 5 + [100] + [400] * 42)
        j = job(runtime=2, deadline=6)
        self.assertIs(s.decide(j, [r], 4.0), r)

    def test_end_to_end_meets_deadline_and_waits_for_dip(self):
        trace = [300] * 5 + [100] * 3 + [400] * 40
        r = region("R", trace)
        m = simulate(ThresholdScheduler(), [r],
                     [job(runtime=2, deadline=20)])
        res = m.get_results()[0]
        self.assertEqual(res["start_time"], 5.0)
        self.assertFalse(res["sla_violated"])


# ============================================================
# TRACE WORKLOAD
# ============================================================

class TraceWorkloadTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from experiments.trace_workload import make_trace_workload
        cls.jobs = make_trace_workload(
            0, ("India", "Germany", "Norway"), fraction=0.002
        )

    def test_sample_size_and_order(self):
        self.assertGreater(len(self.jobs), 800)
        arrivals = [j.arrival_time for j in self.jobs]
        self.assertEqual(arrivals, sorted(arrivals))

    def test_job_attributes_are_valid(self):
        for j in self.jobs:
            self.assertGreaterEqual(j.runtime, 5 / 60 - 1e-9)
            self.assertTrue(1 <= j.cpu_required <= 64)
            self.assertGreater(j.deadline, j.arrival_time + j.runtime)
            self.assertIn(j.home_region, ("India", "Germany", "Norway"))
            self.assertGreaterEqual(j.data_gb, 0)
            if j.allowed_regions:
                self.assertEqual(set(j.allowed_regions), {j.home_region})

    def test_deterministic_per_seed(self):
        from experiments.trace_workload import make_trace_workload
        again = make_trace_workload(
            0, ("India", "Germany", "Norway"), fraction=0.002
        )
        self.assertEqual([j.job_id for j in again][:50],
                         [j.job_id for j in self.jobs][:50])
        self.assertEqual([j.data_gb for j in again][:50],
                         [j.data_gb for j in self.jobs][:50])


if __name__ == "__main__":
    unittest.main()
