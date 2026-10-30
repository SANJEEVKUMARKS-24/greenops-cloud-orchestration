"""
build_review_2.py
Generates the Project Review 2 Report:
Focus: 50% to 60% of Implementation Progress, Core Simulation Architecture, Baseline Benchmarking, Bug Corrections & Review 3 Roadmap.
NOTE: Per user instructions, greenops_architecture.png IS embedded in this Review 2 document.
"""

import os
from docx.shared import Inches, Pt, RGBColor
from report_builder import (
    create_base_doc, add_cover_page, add_h1, add_h2, add_h3,
    add_p, add_bullet, add_table, add_image, save_and_convert
)

def build_review_2():
    doc = create_base_doc("GreenOps Cloud Orchestration — Review 2 Report")

    # Cover Page
    add_cover_page(
        doc,
        review_num="2",
        review_stage_title="Review 2",
        review_sub="Mid-Term Progress Report: 50%–60% Implementation, Simulation Engine & Baseline Benchmarking"
    )

    # Executive Summary / Audit
    add_h1(doc, "Executive Summary & Review 2 Milestone Audit")
    add_p(
        doc,
        "This Review 2 report documents the mid-term progress of the GreenOps project, formally verifying that 50% to 60% "
        "of the planned system implementation has been completed, tested, and validated. Since the approval of the Review 1 "
        "conceptual framework, our team has transformed the theoretical mathematical formulations into a functional, highly "
        "modular discrete-event simulation platform powered by SimPy."
    )
    add_p(
        doc,
        "Specifically, the core simulation engine, heterogeneous workload generator, real-world historical grid carbon trace "
        "pipeline, calibrated forecast error generator, and four comparative baseline schedulers have been fully implemented. "
        "Furthermore, initial versions of both weighted-sum and Pareto-knee GreenOps algorithms have been developed and subjected "
        "to rigorous debugging. A preliminary five-job benchmark and initial 100-job stress tests have been executed to evaluate "
        "the physical power models and verify scheduler invariants. The remaining 40%–50% of the project scope—comprising large-scale "
        "multi-seed statistical validation (20 seeds x 2 seasons), Alibaba cluster trace replay (45,000 jobs), sensitivity sweeps, "
        "and an interactive web operations dashboard—is scheduled for completion in Review 3."
    )

    # Section 1
    add_h1(doc, "1. Review 1 Recap & Alignment of Scope")
    add_p(
        doc,
        "As established in Review 1, cloud datacenters contribute heavily to global greenhouse gas emissions due to rigid, carbon-blind "
        "scheduling policies. While prior works evaluate spatial or temporal shifting in isolation, GreenOps is formulated as a unified "
        "spatio-temporal optimization problem. The core objective is to minimize physical operational carbon emissions C(x) and financial "
        "compute costs K(x) without violating hard customer SLAs (deadlines), budgetary ceilings, or statutory data residency boundaries."
    )
    add_p(
        doc,
        "During this mid-term phase, the project scope was structured to achieve three core milestones: (1) establish a high-fidelity "
        "simulation environment driven by authentic empirical grid data, (2) implement standard and competitive baseline schedulers, "
        "and (3) identify and correct any underlying simulator defects prior to launching large-scale statistical experiments."
    )

    # Section 2
    add_h1(doc, "2. System Architecture and Component Interaction")
    add_p(
        doc,
        "The end-to-end architecture of GreenOps has been fully realized in software. Figure 2.1 illustrates the structural pipeline, "
        "delineating the interaction between the workload manager, carbon forecasting subsystem, the multi-objective decision engine, "
        "and the distributed SimPy execution engine."
    )

    # Embed Architecture Image
    arch_img_path = r"c:\Users\sanje\Desktop\greenops-cloud-orchestration\greenops_architecture.png"
    add_image(
        doc,
        arch_img_path,
        caption="Figure 2.1: End-to-End GreenOps Architecture and Multi-Objective Decision Pipeline",
        width_in=6.0
    )

    add_h2(doc, "2.1 Architectural Workflow Walkthrough")
    add_p(
        doc,
        "As depicted in Figure 2.1, the operational lifecycle of a workload within GreenOps proceeds through five discrete stages:",
        bold_prefix="Decision Lifecycle: "
    )
    add_bullet(
        doc,
        "The workload manager ingests synthetic or trace-derived job specifications. Each job is stamped with arrival time t, "
        "runtime d_j, required CPU cores, memory, hard deadline D_j, budget B_j, carbon priority p_j, and allowed geographical regions A_j.",
        bold_prefix="1. Workload Ingestion & Tagging: "
    )
    add_bullet(
        doc,
        "The carbon pipeline supplies current and forecast carbon intensity data. A horizon-dependent noise generator injects "
        "calibrated error sigma(h) with AR(1) temporal autocorrelation to reflect authentic forecast uncertainty.",
        bold_prefix="2. Carbon Signal Ingestion: "
    )
    add_bullet(
        doc,
        "The decision engine checks data residency, regional hardware capacities, budget feasibility, and latest start time L_j. "
        "Infeasible options are strictly pruned, eliminating SLA or budget violations at the root.",
        bold_prefix="3. Hard Constraint Enforcement: "
    )
    add_bullet(
        doc,
        "For each feasible region and candidate start hour s in [t, min(t+W, L_j)], the engine computes forecast carbon C(x) with "
        "confidence gating (1 + kappa * sigma), monetary cost K(x), and convex SLA risk R(x) = ((s-t)/(L_j-t))^2.",
        bold_prefix="4. Spatio-Temporal Candidate Evaluation: "
    )
    add_bullet(
        doc,
        "If immediate execution (s = t) is optimal and capacity is free, the job is dispatched to the target region. If deferral is "
        "optimal, the job sleeps. If deferral exceeds one hour, the job wakes up every elapsed hour to query refreshed forecasts and "
        "re-evaluate placement.",
        bold_prefix="5. Dispatch & Rolling Re-Planning: "
    )

    # Section 3
    add_h1(doc, "3. Implementation Status (50%–60% Completion Stage)")
    add_p(
        doc,
        "The codebase has been engineered into a clean, modular Python 3.14 package adhering to strict software engineering standards. "
        "Table 3.1 provides an audit of all modules completed during this phase."
    )

    # Table 3.1
    headers_31 = ["Module / Component", "File Location", "Implementation Status", "Verification / Test Coverage"]
    rows_31 = [
        ["Job & Region Data Classes", "sim/job.py, sim/region.py", "100% Completed", "Unit tested in tests/test_greenops.py"],
        ["Carbon Forecaster & Noise Engine", "sim/forecaster.py", "100% Completed", "Calibrated against UK National Grid ESO benchmarks"],
        ["Cloud Discrete-Event Simulator", "sim/simulator.py", "100% Completed", "SimPy 4.1 engine with dynamic resource allocation"],
        ["Workload Generator", "data/generate_workload.py", "100% Completed", "Generates Strict, Batch, and Flexible workload profiles"],
        ["Carbon Trace Pipeline", "data/fetch_carbon_traces.py", "100% Completed", "Energy-Charts API & National Grid ESO scraper"],
        ["Round Robin Baseline", "schedulers/round_robin.py", "100% Completed", "Cyclic spreading baseline operational"],
        ["Cost-Only Baseline", "schedulers/cost_only.py", "100% Completed", "Cheapest feasible placement baseline operational"],
        ["Greenest Region Baseline", "schedulers/greenest_region.py", "100% Completed", "Greedy spatial carbon baseline operational"],
        ["Temporal Green Baseline", "schedulers/temporal_green.py", "100% Completed", "Greedy spatio-temporal baseline operational"],
        ["GreenOps MOO Engine", "schedulers/greenops_moo.py", "100% Completed (Core)", "Weighted sum & Pareto Tchebycheff knee modes"]
    ]
    add_table(doc, headers_31, rows_31, col_widths=[1.7, 1.8, 1.4, 2.1], caption="Table 3.1: Mid-Term Implementation Status and Module Audit")

    add_h2(doc, "3.1 Workload Model Implementation")
    add_p(
        doc,
        "The workload generator (data/generate_workload.py) produces three distinct classes of synthetic jobs with size-proportional "
        "budgets and realistic slack distributions (Table 3.2). 25% of all jobs are pinned to a single home region to represent "
        "sovereign data-residency laws (e.g., European GDPR or Indian personal data localization). For these pinned jobs, spatial shifting "
        "is legally barred, isolating temporal shifting as the sole mechanism for emissions reduction."
    )

    # Table 3.2
    headers_32 = ["Workload Class", "Mix Share", "vCPU Demand", "Runtime (h)", "Deadline Slack (h)", "Budget Multiplier", "Carbon Priority"]
    rows_32 = [
        ["Strict Real-Time (API)", "40%", "1–4 vCPU", "1–3 h", "2–5 h (Never Deferred)", "1.3x–2.2x cheapest", "0.2–0.6"],
        ["Batch Analytics (ETL)", "35%", "2–8 vCPU", "2–6 h", "5–10 h", "1.1x–2.0x cheapest", "0.5–0.8"],
        ["Flexible ML Training", "25%", "2–8 vCPU", "2–6 h", "8–16 h", "1.05x–1.9x cheapest", "0.7–1.0"]
    ]
    add_table(doc, headers_32, rows_32, col_widths=[1.6, 0.9, 1.1, 1.0, 1.4, 1.4, 1.1], caption="Table 3.2: Implemented Workload Class Parameters")

    add_h2(doc, "3.2 Resolution of Critical Simulator Defects")
    add_p(
        doc,
        "Scaling from preliminary five-job prototypes to multi-hundred job simulations exposed several subtle simulation defects. "
        "Identifying and resolving these defects formed a crucial part of our mid-term effort:",
        bold_prefix="Defect Analysis & Fixes: "
    )
    add_bullet(
        doc,
        "In preliminary scripts, jobs that could not immediately acquire capacity were printed and dropped, yet the completed counter "
        "incremented. This was corrected: jobs now wait in a priority queue until hardware resources are released, tardiness is logged, "
        "and only unresolvable constraint violations are formally rejected.",
        bold_prefix="1. Silently Dropped Jobs: "
    )
    add_bullet(
        doc,
        "Drawing budgets uniformly at random resulted in 26% of synthetic jobs being mathematically unaffordable in every available region. "
        "Budgets were recalibrated to scale proportionally with the minimum achievable compute cost in the job's allowed regions.",
        bold_prefix="2. Budget Calibration Disconnect: "
    )
    add_bullet(
        doc,
        "The decision engine estimated energy as CPU cores * runtime, while the execution simulator applied idle power scaling and PUE. "
        "Both modules were harmonized to use the exact same regional power equations: Power = u * P_idle + u * (P_max - P_idle), multiplied by PUE.",
        bold_prefix="3. Inconsistent Energy Models: "
    )
    add_bullet(
        doc,
        "In earlier runs, co-located jobs each paid the datacenter's full idle baseload power. Idle power is now shared proportionally "
        "among concurrently executing jobs based on their fractional CPU allocation.",
        bold_prefix="4. Shared Idle Power Accounting: "
    )
    add_bullet(
        doc,
        "Emissions were originally calculated using only the carbon intensity at the start hour. The engine now integrates the time-weighted "
        "average carbon intensity across the entire execution window [start, start + duration].",
        bold_prefix="5. Window-Averaged Carbon Accounting: "
    )

    # Section 4
    add_h1(doc, "4. Preliminary Benchmarking & Results")
    add_p(
        doc,
        "To validate the corrected simulation engine, the five-job benchmark was re-executed under controlled 24-hour carbon traces "
        "(Table 4.1). All five schedulers operated with zero SLA violations under this controlled scenario."
    )

    # Table 4.1 Benchmark
    headers_41 = ["Scheduler Policy", "Carbon (gCO2eq)", "Energy (kWh)", "Cost ($)", "SLA Violations", "Avg Latency (h)", "Preliminary g (Pre-Fix)"]
    rows_41 = [
        ["Round Robin", "565.2", "1.36", "3.46", "0", "2.0", "673.5"],
        ["Cost Only", "1113.2", "1.76", "2.56", "0", "2.0", "1146.0"],
        ["Greenest Region", "92.4", "0.97", "4.48", "0", "2.0", "182.0"],
        ["Temporal Green", "82.1", "0.97", "4.48", "0", "2.8", "140.0"],
        ["GreenOps MOO (This Work)", "92.4", "0.97", "4.48", "0", "2.0", "258.5"]
    ]
    add_table(doc, headers_41, rows_41, highlight_idx=4, caption="Table 4.1: Re-Run of Preliminary 5-Job Benchmark on Corrected Simulator")

    add_h2(doc, "4.1 Key Observations from Mid-Term Benchmarking")
    add_p(
        doc,
        "The preliminary results provide three vital insights:",
        bold_prefix="Core Findings: "
    )
    add_bullet(
        doc,
        "Cost-Only scheduling is ecologically disastrous: by routing exclusively to the cheapest region (India), it emits 1,113.2 gCO2eq, "
        "representing more than a 12-fold increase over carbon-aware policies.",
        bold_prefix="1. Cost Optimization Penalty: "
    )
    add_bullet(
        doc,
        "In unconstrained five-job tests with low utilization, spatial shifting to clean regions (Norway) captures the vast majority of "
        "available carbon reductions (reducing emissions from 565 g down to 92 g).",
        bold_prefix="2. Dominance of Spatial Shifting Under Low Load: "
    )
    add_bullet(
        doc,
        "Initial 100-job stress runs reveal that when Norway's hardware capacity saturates, pure spatial schedulers are forced to spill "
        "over into dirty grids. This is precisely where GreenOps' temporal shifting provides decisive advantages, deferring flexible jobs "
        "to wait for renewable surges in Germany or capacity releases in Norway.",
        bold_prefix="3. Emergence of Capacity Bottlenecks: "
    )

    # Section 5
    add_h1(doc, "5. Remaining Work and Detailed Roadmap for Review 3")
    add_p(
        doc,
        "With the core architecture, simulation engine, and baseline schedulers fully functional (representing ~55% completion), "
        "the remaining effort will be dedicated to comprehensive empirical evaluation, real trace replay, and operator tooling for Review 3."
    )

    add_h2(doc, "5.1 Planned Work Packages for Review 3")
    add_bullet(
        doc,
        "Execute 40 paired simulation runs across 20 random seeds and two distinct seasons (Winter January and Summer July 2024). "
        "Apply two-sided paired permutation tests to establish statistical significance (p < 0.001).",
        bold_prefix="Work Package 1: Large-Scale Multi-Seed Evaluation (E1): "
    )
    add_bullet(
        doc,
        "Conduct a 66-point weight sweep over the objective simplex to trace the complete 3D Pareto frontier and calculate 2D "
        "normalized hypervolume against all combined baselines.",
        bold_prefix="Work Package 2: Pareto Hypervolume Analysis (E2): "
    )
    add_bullet(
        doc,
        "Systematically evaluate forecast error sensitivity (0% to 50% relative RMSE), deferral window limits (0 to 24 hours), "
        "arrival load multipliers (0.5x to 3.0x), and extended six-region scaling.",
        bold_prefix="Work Package 3: Sensitivity & Boundary Characterization (E3–E6): "
    )
    add_bullet(
        doc,
        "Replay ~45,000 real jobs from the Alibaba 2018 cluster trace, incorporating a formal WAN network data-transfer model "
        "(0.005 kWh/GB, $0.02/GB, 1 Gbit/s bandwidth) and benchmarking against published literature baselines (Wait Awhile and Online Threshold).",
        bold_prefix="Work Package 4: Real-World Alibaba Cluster Trace Replay: "
    )
    add_bullet(
        doc,
        "Deploy a self-contained web operations dashboard featuring real-time job dispatching, multi-policy benchmark runners, "
        "live 24-hour grid carbon sparklines, and an interactive Gantt scheduling timeline.",
        bold_prefix="Work Package 5: Interactive Cloud Operations Dashboard: "
    )

    # Section 6
    add_h1(doc, "6. Milestone Tracking and Deliverables Schedule")
    headers_61 = ["Project Phase", "Scope & Deliverables", "Target Review", "Completion Status"]
    rows_61 = [
        ["Phase 1: Conceptual Design", "Problem formulation, mathematical models, literature review", "Review 1", "100% Completed"],
        ["Phase 2: Simulation Core", "SimPy multi-region engine, power models, PUE calculations", "Review 2", "100% Completed"],
        ["Phase 3: Workload & Traces", "3-tier workload generator, Energy-Charts & NG-ESO trace pipeline", "Review 2", "100% Completed"],
        ["Phase 4: Schedulers & Baselines", "Round Robin, Cost Only, Greenest Region, Temporal Green, GreenOps MOO", "Review 2", "100% Completed"],
        ["Phase 5: Simulator Debugging", "Fixed dropped jobs, budget scale, idle power share, window carbon", "Review 2", "100% Completed"],
        ["Phase 6: Multi-Seed Experiments", "20 seeds x 2 seasons, statistical permutation tests, E1–E7 sweeps", "Review 3", "Scheduled"],
        ["Phase 7: Alibaba Trace Replay", "45,000 jobs replay, WAN data transfer modeling, literature baselines", "Review 3", "Scheduled"],
        ["Phase 8: Web Dashboard & UI", "Interactive browser dashboard, live Gantt chart, sparklines", "Review 3", "Scheduled"]
    ]
    add_table(doc, headers_61, rows_61, col_widths=[1.6, 2.7, 1.1, 1.3], caption="Table 6.1: Project Progress Across Evaluation Milestones")

    # References
    add_h1(doc, "References")
    refs = [
        "B. Acun, B. Lee, F. Kazhamiaka, K. Maeng, U. Gupta, M. Chakkaravarthy, D. Brooks, and C.-J. Wu, 'On the Limitations of Carbon-Aware Temporal and Spatial Workload Shifting in the Cloud,' in Proceedings of the Nineteenth European Conference on Computer Systems (EuroSys '24), pp. 924–941, 2024.",
        "P. Wiesner, I. Behnke, D. Scheinert, K. Gontarska, and L. Thamsen, 'Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud,' in Proceedings of the 22nd International Middleware Conference (Middleware '21), pp. 260–272, 2021.",
        "A. Radovanović et al., 'Carbon-Aware Computing for Datacenters,' IEEE Transactions on Power Systems, vol. 38, no. 2, pp. 1270–1280, 2023.",
        "A. Lechowicz et al., 'Learning-Augmented Competitive Algorithms for Spatiotemporal Online Allocation with Deadline Constraints,' in Proceedings of ACM SIGMETRICS, 2024.",
        "W. A. Hanafy, Q. Liang, N. Bashir, D. Irwin, and P. Shenoy, 'CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency,' Proc. ACM Meas. Anal. Comput. Syst., vol. 7, no. 3, 2023.",
        "Z. Zhou et al., 'Carbon-Aware Load Balancing for Geo-Distributed Cloud Services,' in IEEE MASCOTS, 2013."
    ]
    for r in refs:
        add_bullet(doc, r)

    # Output paths
    docx_path = os.path.abspath("GreenOps_Review_2_Report.docx")
    pdf_path = os.path.abspath("GreenOps_Review_2_Report.pdf")
    save_and_convert(doc, docx_path, pdf_path)

if __name__ == "__main__":
    build_review_2()
