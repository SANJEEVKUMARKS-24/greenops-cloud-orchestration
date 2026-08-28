# GreenOps Cloud Orchestration — Execution Plan

A step-by-step technical roadmap for building and validating the Multi-Objective Carbon-Aware Scheduler described in your proposal.

---

## 0. Framing the Project Correctly Before You Write Code

This is fundamentally a **simulation + optimization** project, not a live-infrastructure project. You are not going to actually move workloads across real AWS/GCP regions — you're going to build a discrete-event simulator that *stands in* for a multi-region cloud, feed it real carbon-intensity traces, and prove that your scheduling heuristic beats naive baselines on emissions without blowing SLA or cost budgets.

Keep that framing explicit in your head at every stage: **simulator fidelity + heuristic quality + evaluation rigor** are the three things that will actually get judged (by a reviewer, a professor, or a patent evaluator). Nothing here needs GPU-heavy training, so this is comfortably within a laptop-class setup — the bottleneck will be simulation design and experiment volume, not compute.

---

## 1. Phase Breakdown

### Phase 1 — Literature Positioning (3–5 days)
Before writing a line of simulator code, nail down **exactly what gap you're filling**, because paper #1 in your list (Acun et al., EuroSys'24, "On the Limitations of Carbon-Aware Temporal and Spatial Workload Shifting") already shows that naive shifting has limited real-world upside. You need to read that paper *first and most carefully* — it will either become your main foil (baseline to beat) or force you to narrow your claim.

Action items:
- Read papers #1, #4, #12, #17 closely (these are the ones doing joint spatial+temporal shifting with formal guarantees or negative results).
- Build a one-page "gap table": columns = [paper, spatial?, temporal?, joint optimization?, SLA-aware?, cost-aware?, open-source harness?, evaluation dataset]. This table becomes your related-work section for free later.
- Decide your specific differentiator. Realistic candidates given your list:
  - Most papers do spatial *or* temporal shifting well but treat the third axis (cost) as an afterthought — your three-way Pareto-aware heuristic (carbon + cost + SLA jointly) is a legitimate angle if you keep it tight.
  - An **open, reproducible simulation harness** combining real carbon traces + configurable workload traces (contribution #2 in your abstract) is itself a publishable/patentable artifact if no one else's is public and usable.

**Deliverable:** a 1-page "positioning memo" — what's been done, what's missing, what you're claiming.

---

### Phase 2 — Data Acquisition (3–7 days)

You need two independent data feeds:

**A. Carbon intensity traces (per region, per hour)**
- Primary: [Electricity Maps API](https://www.electricitymaps.com/) (free tier gives historical + live data per country/region — good granularity, well documented).
- Alternative/cross-check: WattTime API (needs registration, US-focused, marginal emissions data — arguably more correct for "what happens if I shift load" than average intensity).
- Green Software Foundation's **Carbon Aware SDK** wraps both of the above with a common interface — use it if you want vendor-agnostic queries, or go direct-to-API if you want tighter control over caching/rate limits.
- Pull at least 3–6 regions with genuinely different generation mixes (e.g., a hydro/nuclear-heavy region, a coal-heavy region, a solar-heavy region with strong diurnal swing) — the whole "spatial shifting" story is only interesting if the regions actually differ.
- Pull at least 2–4 weeks of hourly data per region so your temporal-shifting story has real diurnal/weekly cyclicality to exploit.

**B. Workload traces**
- Don't hand-roll everything synthetically — ground at least one workload class in a real trace for credibility:
  - Google Cluster Data (2019 trace) or Alibaba Cluster Trace for batch/analytics-style jobs.
  - Azure Public Dataset (VM workload traces) for elastic/deferrable workloads.
- Synthesize the rest (real-time inference APIs = strict low-latency, Poisson-ish arrivals; deadline-bound batch = arrival + deadline offset; fully deferrable = arrival + large slack window). Parameterize flexibility class explicitly per job.

**Deliverable:** a `data/` folder with cleaned, timestamp-aligned carbon traces per region and a workload generator/loader module with a documented schema (job_id, arrival_time, est_runtime, resource_req, sla_deadline, flexibility_class, region_locality_constraint).

---

### Phase 3 — Simulator Architecture (1–2 weeks)

Use **SimPy** (Python discrete-event simulation library) — it's the standard choice for this exact class of problem (job arrival → resource contention → completion events), lightweight, and every reviewer in this subfield will recognize it.

Core entities to model:
- `Region` — has a compute capacity, a live/forecast carbon-intensity signal (from Phase 2 data), a cost-per-unit-compute signal, and a running queue/utilization state.
- `Job` — arrival time, resource demand, runtime estimate, SLA deadline, flexibility class, optional data-locality constraint (which regions it's even allowed to run in).
- `Scheduler` — the pluggable decision-making component. This is where your heuristic and every baseline live, all implementing the same interface (`decide(job, candidate_regions, current_time) -> (region, start_time)`), so swapping schedulers is a one-line change in your experiment driver.
- `Clock/Event loop` — SimPy's environment; advances time, triggers job arrivals, resource-freeing events, and periodic re-evaluation of deferred jobs.

Suggested repo layout:
```
greenops-sim/
├── data/
│   ├── carbon_traces/{region}.csv
│   └── workload_traces/
├── sim/
│   ├── region.py
│   ├── job.py
│   ├── clock.py
│   └── engine.py            # SimPy environment wiring
├── schedulers/
│   ├── base.py              # abstract Scheduler interface
│   ├── round_robin.py       # baseline
│   ├── cost_only.py         # baseline
│   ├── greenest_region.py   # greedy baseline
│   └── carbon_aware_moo.py  # your contribution
├── metrics/
│   └── collector.py         # gCO2eq, SLA violations, cost, latency
├── experiments/
│   └── run_experiment.py    # CLI: pick scheduler + trace + params
└── notebooks/
    └── analysis.ipynb
```

**Deliverable:** a working simulator that can run the *round-robin baseline* end-to-end and emit metrics. Get this trivial case running before touching the real heuristic — it validates your event loop and metric collection independently of algorithmic complexity.

---

### Phase 4 — The Scheduling Heuristic (2–3 weeks, the core contribution)

You have two honest options for the "multi-objective" core — pick one deliberately, don't hand-wave between them:

**Option A — Weighted-sum scalarization (simpler, faster to implement and defend)**
For each candidate (region, start_time) pair, compute a score:
```
score = w_carbon · normalized_carbon(region, t)
      + w_cost   · normalized_cost(region, t)
      + w_sla    · sla_risk_penalty(job, region, t)
```
Choose the option minimizing score, subject to a **hard constraint** that SLA deadline is never violated (this constraint, not the weight, is what actually protects your latency-critical jobs — make that explicit in the writeup, since reviewers will ask).
- Pros: implementable in days, easy to explain, easy to sweep weights for a sensitivity analysis (which becomes a nice figure).
- Cons: reviewers may push back on scalarization as "not really multi-objective optimization."

**Option B — True Pareto-frontier approach**
At each decision point, enumerate feasible (region, start_time) options, compute the Pareto front over (carbon, cost, SLA-slack), and pick via a secondary rule (e.g., knee-point selection, or lexicographic: SLA-feasible first, then minimize carbon, tie-break on cost).
- Pros: matches the "Pareto-aware heuristic" language in your own abstract, stronger theoretical story, differentiates you more clearly from weighted-sum baselines already in the literature (several of your 20 papers do weighted-sum).
- Cons: more implementation work, harder to explain in limited paper space, needs care around what "Pareto-aware" evaluation criterion you report (hypervolume indicator is the standard metric here if you want a rigorous multi-objective evaluation).

Recommendation: **implement Option A first to get end-to-end results fast, then upgrade to Option B if time allows** — Option B with a hypervolume-based evaluation is what will make this paper stand out relative to papers #7, #9, #14 in your list, which look more weighted-sum/greedy.

Two concrete algorithmic pieces to build:
1. **Spatial shifting logic** — at job arrival, filter candidate regions by locality/latency constraints, then rank by current+forecast carbon intensity.
2. **Temporal shifting logic** — for deferrable jobs, don't decide immediately; hold in a queue and re-evaluate at each simulation tick whether "run now" vs. "wait" is better, using the forecast curve and remaining slack to deadline. This is the part most papers under-implement — a clean, forecast-aware "wait vs run now" decision rule (not just "run whenever carbon is below a fixed threshold") is a defensible novelty claim.

**Deliverable:** `carbon_aware_moo.py` scheduler passing unit tests against synthetic edge cases (job with zero slack must never be deferred past deadline; job with huge slack should wait for a clearly better carbon window if one exists in the trace).

---

### Phase 5 — Baselines (3–5 days)

Implement these exactly as named in your evaluation plan, no more, no less — reviewers will map your results table directly onto this list:
1. Carbon-agnostic round-robin / bin-packing (Kubernetes-default-like behavior).
2. Cost-only scheduler (always pick cheapest eligible region/time).
3. Greedy "always pick greenest region" (spatial-only, no temporal shifting, no cost awareness) — this isolates how much your temporal component and cost-awareness are actually contributing versus naive greening.

Keeping these minimal and clean matters more than adding extra baselines — a clean 4-way comparison (3 baselines + yours) is easier to present convincingly than a cluttered 8-way one.

---

### Phase 6 — Evaluation & Metrics (1–2 weeks)

Metrics to instrument (all four from your proposal, plus two extras that reviewers commonly expect):
- **Total gCO2eq emitted** (primary metric)
- **SLA violation rate** (%, and also worth reporting violation *severity* — how late, not just binary)
- **Cost overhead** (relative to cost-only baseline, %)
- **Job completion latency** (mean + p95/p99 — tail latency matters a lot for the "strict real-time" workload class)
- *(extra)* **Carbon-cost trade-off curve** — sweep your weighting parameter (or Pareto knee-point rule) and plot the resulting frontier; this single figure often carries an entire results section.
- *(extra)* **Sensitivity to forecast error** — degrade the carbon forecast signal with synthetic noise and show how gracefully your scheduler degrades vs. the greedy baseline. This directly engages with paper #1's central critique (that shifting benefits evaporate under realistic forecast uncertainty) and turns a potential weakness into a demonstrated strength if your method holds up better than greedy under noise.

Run each scheduler across:
- Multiple random seeds (workload arrival randomness) — report mean ± std, not single runs.
- At least 2 distinct carbon-trace periods (e.g., a season with high renewable variance vs. one with low variance) to show your gains aren't trace-specific.

**Deliverable:** a results table (scheduler × metric) + 3–4 figures (bar chart of emissions by scheduler, latency CDF, cost-carbon Pareto sweep, forecast-noise sensitivity).

---

### Phase 7 — Writing (concurrent with Phase 6, finalized after)

Structure to match your existing abstract almost 1:1 — you've essentially already written the abstract and intro:
1. Introduction / Motivation (mostly done — polish from your proposal text)
2. Related Work (built directly from your Phase 1 gap table)
3. System Design (Phase 3–4 architecture, with a clear diagram of the scheduler's decision loop)
4. Scheduling Heuristic (formalize whichever of Option A/B you built — include the actual objective function/constraint formulation, not just prose)
5. Evaluation (Phase 6 results)
6. Discussion / Limitations — **engage directly with the Acun et al. critique here.** Explicitly stating where your method's gains shrink or vanish is what separates a defensible paper from an oversold one, and reviewers who know that paper will look for exactly this section.
7. Conclusion + Future Work

Target venue framing: this fits workshop/track venues like GreenNet, HotCarbon, EuroSys workshops, or a sustainability-track submission at a systems conference — worth checking current CFPs once the results are in, since fit determines page limit and required rigor level.

---

### Phase 8 — Patent-Layer Extraction (optional, after paper draft is stable)

If you want to mirror your usual project structure (paper + separate IP-oriented extraction), the most defensible claim here is likely **not** "carbon-aware scheduling" in the abstract (too broad, heavily prior-arted by your own reference list) but a specific, narrow mechanism, e.g.:
- The specific **forecast-aware temporal "wait vs. run now" decision rule** (if it has a novel mathematical form beyond simple threshold-crossing).
- The **joint three-signal (carbon + cost + SLA) real-time re-evaluation loop** for already-queued deferred jobs, if your re-evaluation mechanism is architecturally distinct from prior art.
Do the patent-landscape check on these narrow claims specifically (not "carbon-aware cloud scheduling" broadly) before investing writing time here.

---

## 2. Suggested Timeline (assuming part-time, alongside coursework)

| Week | Focus |
|---|---|
| 1 | Literature positioning memo + finalize data sources |
| 2 | Pull/clean carbon + workload traces |
| 3–4 | Simulator skeleton (SimPy) + round-robin baseline running end-to-end |
| 5–6 | Cost-only + greedy-greenest baselines; metrics collector finalized |
| 7–9 | Carbon-aware MOO scheduler (Option A first, then B if time allows) |
| 10 | Full experiment sweep (seeds × traces × schedulers) |
| 11 | Analysis, figures, forecast-noise sensitivity study |
| 12+ | Paper writing, positioning against Acun et al. critique, optional patent memo |

---

## 3. Key Risks / Things to Get Ahead Of

- **Risk:** Acun et al. (EuroSys'24) may already show your exact claim doesn't hold in practice → mitigate by reading it in week 1, not week 10, and be ready to narrow scope (e.g., "under X workload mix / X forecast quality, gains persist") rather than discovering this late.
- **Risk:** Synthetic-only workloads look weak to reviewers → ground at least one class in a real cluster trace (Phase 2B).
- **Risk:** Weighted-sum scalarization gets dismissed as "not really multi-objective" → have the Pareto/hypervolume evaluation ready even if the scheduler itself uses scalarization, so your *evaluation* is rigorous even if the *heuristic* is simple.
- **Risk:** Carbon API rate limits / access changes mid-project → cache all pulled trace data locally on day one; never depend on live API calls during simulation runs.

---

## 4. Tech Stack Summary

- **Simulation:** Python + SimPy
- **Data:** Electricity Maps API / WattTime / Carbon Aware SDK (traces), Google/Alibaba/Azure cluster traces (workloads)
- **Analysis:** pandas, matplotlib/seaborn, optionally `pymoo` if you want off-the-shelf Pareto/hypervolume utilities for Option B
- **Compute needs:** CPU-only, single laptop is sufficient — this is not a GPU-bound project, so your hardware isn't a constraint here.
