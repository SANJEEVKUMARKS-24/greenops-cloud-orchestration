"""
build_review_3.py
Generates the Project Review 3 Report:
Focus: Complete Final Project Report (100% Completion).
Includes: Full mathematical formulation, embedded architecture diagram (greenops_architecture.png),
complete evaluation figures (fig1-fig8), all tables, Alibaba trace replay, dashboard details,
statistical defense, discussion, and reproduction guide.
"""

import os
from docx.shared import Inches, Pt, RGBColor
from report_builder import (
    create_base_doc, add_cover_page, add_h1, add_h2, add_h3,
    add_p, add_bullet, add_table, add_image, save_and_convert
)

def build_review_3():
    doc = create_base_doc("GreenOps Cloud Orchestration — Final Project Report (Review 3)")

    # Cover Page
    add_cover_page(
        doc,
        review_num="3",
        review_stage_title="Review 3 (Final Defense)",
        review_sub="Comprehensive Final Project Report: End-to-End System Implementation, Large-Scale Trace Replay & Multi-Objective Defense"
    )

    # Abstract / Executive Summary
    add_h1(doc, "Abstract")
    add_p(
        doc,
        "Cloud datacenters represent a rapidly escalating share of global electrical energy consumption. Conventional workload "
        "schedulers optimize exclusively for execution turnaround time, hardware resource packing, and monetary cost, completely "
        "disregarding the time-varying carbon intensity of the electrical grids powering them. Because electrical grid emission factors "
        "diverge dramatically across geographical regions and across the hours of a day, identical computational workloads produce "
        "radically different carbon footprints depending purely on where and when they execute."
    )
    add_p(
        doc,
        "This project presents GreenOps, a production-grade multi-objective cloud orchestration framework that dynamically unifies "
        "spatial demand shifting (routing workloads to geographically cleaner regions) with forecast-aware temporal demand shifting "
        "(deferring delay-tolerant batch computations to greener hours). GreenOps jointly balances forecast carbon emissions, financial "
        "compute costs, and convex SLA risk while enforcing customer deadlines, budgetary ceilings, and statutory data residency laws "
        "as non-negotiable hard constraints."
    )
    add_p(
        doc,
        "The system is implemented in Python 3.14 with SimPy and evaluated against real-world historical grid carbon traces for January "
        "and July 2024 across six countries (Germany, Norway, France, Poland, Great Britain, and India). Across 40 paired simulation runs "
        "(20 seeds x 2 seasons, 300 jobs per run), GreenOps achieves a 26.8% carbon reduction compared to carbon-agnostic Round Robin "
        "and a 5.3% reduction over greedy spatial greening (p < 0.001), with only a negligible 0.65% increase in compute cost. It achieves "
        "within 1.2% of an aggressive carbon-greedy temporal baseline while reducing SLA violations by 90% and cutting tail latency in half. "
        "Sweeping objective weights over a 66-point simplex traces a continuous Pareto frontier whose normalized 2D hypervolume (0.754) "
        "significantly surpasses all combined baselines (0.524). A trace-driven evaluation replaying ~45,000 real jobs from the Alibaba 2018 "
        "cluster trace with wide-area data-transfer costs confirms that GreenOps maintains the lowest SLA violation rate of all policies (0.50%). "
        "Finally, an interactive web-based operations dashboard is delivered to facilitate real-time workload dispatching, live Gantt scheduling "
        "visualization, and multi-policy benchmarking."
    )

    # Chapter 1
    add_h1(doc, "1. Introduction & Background")
    add_h2(doc, "1.1 Research Motivation")
    add_p(
        doc,
        "The global datacenter fleet consumes an estimated 240–340 TWh of electricity annually, accounting for 1% to 2% of worldwide "
        "electricity demand and approximately 1% of global greenhouse gas emissions. Driven by exponential advances in generative artificial "
        "intelligence, deep learning model training, and continuous analytics pipelines, this demand is projected to double by 2030. "
        "Historically, cloud orchestrators such as Kubernetes, Slurm, and cloud autoscalers treat power as an infinite, static, and "
        "environmentally uniform resource. However, electrical grids are undergoing rapid transitions characterized by variable renewable "
        "energy (VRE) sources—such as wind and solar—which introduce substantial spatio-temporal volatility into grid carbon intensity."
    )
    add_p(
        doc,
        "Figure 1.1 illustrates the hourly carbon intensity traces across three core regions (India, Germany, Norway) for the first week "
        "of January 2024. The empirical data highlights two fundamental physical realities: (1) spatial disparities are vast, with hydro-rich "
        "Norway averaging 28 gCO2eq/kWh while coal-heavy India averages 708 gCO2eq/kWh; and (2) temporal volatility in renewable grids is severe, "
        "with Germany swinging between 130 and 650 gCO2eq/kWh within 24 hours as solar and wind output waxes and wanes."
    )

    # Embed Fig 1
    fig1_path = "results/figures/fig1_carbon_traces.png"
    add_image(doc, fig1_path, caption="Figure 1.1: Multi-Region Hourly Grid Carbon Intensity Traces (January 2024 Core Dataset)", width_in=5.8)

    add_h2(doc, "1.2 Problem Formulation & The Carbon Trilemma")
    add_p(
        doc,
        "Cloud operators face a fundamental trilemma: how to aggressively reduce physical carbon emissions without inflating cloud bills "
        "or violating Service Level Agreements (SLAs). Prior single-dimensional approaches fail in production: pure spatial shifting is "
        "throttled when green regions saturate, while pure temporal shifting severely inflates queueing latency and breaches deadlines. "
        "Furthermore, day-ahead carbon forecasts suffer from horizon-dependent forecasting error (10%–20% RMSE), causing naive schedulers "
        "to defer jobs into dirty periods. GreenOps overcomes these limitations through unified spatio-temporal modeling, convex SLA risk "
        "penalties, confidence gating, and rolling hourly re-planning."
    )

    add_h2(doc, "1.3 Summary of Contributions")
    add_bullet(
        doc,
        "A SimPy discrete-event simulation framework modeling heterogeneous virtual machine resources, regional utilization-based power curves, "
        "regional Power Usage Effectiveness (PUE) multipliers, monetary billing, and network data gravity.",
        bold_prefix="1. High-Fidelity Multi-Region Simulation Platform: "
    )
    add_bullet(
        doc,
        "A multi-objective decision engine that unifies spatial and temporal shifting over candidate pairs (region x start time), "
        "incorporating convex SLA risk, confidence gating, and dynamic hourly re-planning.",
        bold_prefix="2. Unified Spatio-Temporal Scheduling Engine: "
    )
    add_bullet(
        doc,
        "Multi-week hourly empirical carbon traces for six countries derived from Fraunhofer ISE Energy-Charts and UK National Grid ESO APIs, "
        "coupled with an AR(1) forecast error generator.",
        bold_prefix="3. Authentic Carbon Trace Pipeline & Calibrated Forecaster: "
    )
    add_bullet(
        doc,
        "Rigorous evaluation across 40 paired runs demonstrating a 26.8% carbon cut over Round Robin, a 5.3% cut over greedy greening "
        "(p < 0.001), 90% fewer SLA violations than temporal greed, and superior Pareto hypervolume (0.754 vs 0.524).",
        bold_prefix="4. Statistically Validated Synthetic Benchmarks (E1–E7): "
    )
    add_bullet(
        doc,
        "Trace-driven replay of ~45,000 jobs from the Alibaba 2018 cluster trace with wide-area data movement overhead, outperforming published "
        "literature baselines on SLA compliance.",
        bold_prefix="5. Realistic Trace Replay & Literature Comparison: "
    )
    add_bullet(
        doc,
        "A standalone web application providing real-time job dispatching, multi-scheduler benchmarking, live carbon sparklines, and a Gantt timeline.",
        bold_prefix="6. Interactive Cloud Operations Dashboard: "
    )

    # Chapter 2
    add_h1(doc, "2. Literature Review & Gap Analysis")
    add_p(
        doc,
        "Our work builds upon and synthesizes twenty foundational studies across eight research threads. Table 2.1 contrasts the architectural "
        "capabilities of GreenOps against representative prior state-of-the-art approaches."
    )

    # Table 2.1 Capability Matrix
    headers_21 = ["System / Approach", "Spatial", "Temporal", "Cost Aware", "Hard SLA", "Forecast Error", "Multi-Obj."]
    rows_21 = [
        ["Round Robin (K8s Default)", "Spreading", "No", "No", "No", "Ignored", "No"],
        ["Cost Only Scheduler", "Yes (Cheapest)", "No", "Primary", "No", "Ignored", "No"],
        ["Greenest Region (Greedy Spatial)", "Yes", "No", "No", "No", "Ignored", "No"],
        ["Wait Awhile (Wiesner '21)", "No", "Yes", "Partial", "Partial", "Rarely", "No"],
        ["Temporal Green (Greedy Search)", "No", "Yes", "No", "Violates", "Ignored", "No"],
        ["Google Carbon-Aware ('23)", "Yes", "Yes", "Internal", "Batch only", "Calibrated", "Heuristic"],
        ["Online Threshold (Lechowicz '24)", "Yes", "Yes", "No", "Yes (Online)", "Forecast-free", "Competitive"],
        ["GreenOps (This Project)", "Yes", "Yes", "Yes", "Yes (Hard)", "Modelled + Gated", "Yes (Pareto+Weight)"]
    ]
    add_table(doc, headers_21, rows_21, highlight_idx=7, caption="Table 2.1: Capability Comparison of Schedulers")

    add_h2(doc, "2.1 Research Gaps and GreenOps Solutions")
    headers_22 = ["Identified Research Gap", "Shortcomings in Literature", "GreenOps Proposed Solution"]
    rows_22 = [
        ["Isolated Shifting Dimensions", "Prior works treat spatial and temporal shifting as mutually exclusive mechanisms.", "Joint candidate space (region x start hour) optimized simultaneously under a single decision."],
        ["Lack of Cost & Budget Realism", "Carbon optimizers ignore regional price disparities, causing massive budget blowouts.", "Strict budgetary constraints B_j and normalized cost objectives K(x) integrated directly."],
        ["Catastrophic SLA Violations", "Aggressive green schedulers exhaust deadline slack, doubling tail latencies.", "Convex SLA penalty R(x) and hard deadline feasibility checks guarantee strict timeliness."],
        ["Blind Faith in Forecasts", "Most simulators assume perfect foresight, failing when real weather deviates.", "Calibrated AR(1) error model, confidence gating (kappa*sigma), and hourly rolling re-planning."],
        ["Absence of Pareto Analysis", "Literature is dominated by arbitrary weighted sums without formal trade-off curves.", "Full 66-point simplex sweep tracing continuous Pareto frontiers with hypervolume metrics."]
    ]
    add_table(doc, headers_22, rows_22, col_widths=[1.8, 2.5, 2.5], caption="Table 2.2: Research Gaps and GreenOps Contributions")

    # Chapter 3
    add_h1(doc, "3. System Architecture & Formal Mathematical Formulation")
    add_p(
        doc,
        "Figure 3.1 depicts the comprehensive architecture of GreenOps. The platform bridges grid-level carbon signals with datacenter "
        "execution infrastructure via a five-stage decision pipeline."
    )

    # Embed Architecture Image
    arch_img_path = r"c:\Users\sanje\Desktop\greenops-cloud-orchestration\greenops_architecture.png"
    add_image(doc, arch_img_path, caption="Figure 3.1: Complete GreenOps Architecture and Multi-Objective Decision Pipeline", width_in=6.0)

    add_h2(doc, "3.1 Formal Problem Formulation")
    add_p(
        doc,
        "At decision epoch t, an incoming job j is characterized by runtime d_j, hard deadline D_j, latest start time L_j = D_j - d_j, "
        "cost budget B_j, allowed geographic regions A_j, and carbon priority p_j. The orchestrator enumerates the feasible candidate set X_j(t):"
    )
    add_p(
        doc,
        "X_j(t) = { (r, s) : r in A_j,  Cost_r(j) <= B_j,  s in {t, ceil(t), ..., min(t+W, L_j)},  (s = t => Region r has free capacity) }",
        italic=True
    )
    add_p(
        doc,
        "Each feasible candidate pair x = (r, s) is evaluated against three non-dimensionalized objective functions:",
        bold_prefix="Mathematical Objectives: "
    )
    add_bullet(
        doc,
        "C(x) = E_r(j) * Forecast_CI(r, s, s + d_j) * (1 + kappa * sigma(s - t)). Here, E_r(j) represents the job's energy consumption "
        "in region r, Forecast_CI is the forecast carbon intensity averaged over the execution window, and kappa * sigma represents the "
        "confidence gate penalizing long-horizon forecast uncertainty.",
        bold_prefix="1. Carbon Emissions Objective C(x): "
    )
    add_bullet(
        doc,
        "K(x) = cpu_j * d_j * Price_r, reflecting the financial compute expenditure based on regional hourly vCPU rates.",
        bold_prefix="2. Monetary Compute Cost Objective K(x): "
    )
    add_bullet(
        doc,
        "R(x) = ((s - t) / (L_j - t))^2. This strictly convex penalty ensures that waiting is practically free when remaining deadline slack "
        "is plentiful, but escalates quadratically as the candidate start time approaches the latest start time L_j.",
        bold_prefix="3. Convex SLA Risk Objective R(x): "
    )

    add_h2(doc, "3.2 Candidate Scoring and Selection")
    add_p(
        doc,
        "GreenOps supports two operational selection paradigms:",
        bold_prefix="Operational Modes: "
    )
    add_bullet(
        doc,
        "Score(x) = w_c * p_j * (C(x) / C_max) + w_k * (K(x) / K_max) + w_r * R(x), with default weights (0.6, 0.2, 0.2) and kappa = 0.5. "
        "Ratio-to-max normalization preserves relative physical magnitudes without stretching trivial differences to full scale.",
        bold_prefix="Weighted Sum Mode (Default): "
    )
    add_bullet(
        doc,
        "Filters all candidates down to the non-dominated Pareto frontier and selects the candidate minimizing the weighted Tchebycheff "
        "distance max_i [ w_i * (f_i(x) - f_i^*) / (f_i^N - f_i^*) ] to the utopian ideal point f^*, normalized by the nadir f^N.",
        bold_prefix="Pareto Tchebycheff Knee Mode: "
    )

    add_h2(doc, "3.3 Multi-Region Cloud Configuration")
    add_p(
        doc,
        "Table 3.1 details the multi-region simulation environment. Regions differ in pricing, physical power characteristics, and seasonal carbon intensity."
    )

    # Table 3.1 Region Specs
    headers_31r = ["Region", "$/vCPU-h", "Idle / Max kW", "PUE", "Winter Mean CI", "Summer Mean CI", "Grid Data Source"]
    rows_31r = [
        ["India (IN)", "0.08", "0.12 / 0.55", "1.60", "708 g/kWh", "633 g/kWh", "Modelled (CEA Calibrated)"],
        ["Germany (DE)", "0.11", "0.10 / 0.50", "1.30", "353 g/kWh", "331 g/kWh", "Energy-Charts Generation Mix"],
        ["Norway (NO)", "0.14", "0.08 / 0.42", "1.15", "28 g/kWh", "31 g/kWh", "Energy-Charts Generation Mix"],
        ["France (FR)", "0.12", "0.10 / 0.48", "1.35", "52 g/kWh", "29 g/kWh", "Energy-Charts Generation Mix"],
        ["Poland (PL)", "0.09", "0.11 / 0.52", "1.45", "586 g/kWh", "626 g/kWh", "Energy-Charts Generation Mix"],
        ["Great Britain (GB)", "0.13", "0.10 / 0.48", "1.35", "159 g/kWh", "113 g/kWh", "National Grid ESO Carbon API"]
    ]
    add_table(doc, headers_31r, rows_31r, col_widths=[1.3, 0.9, 1.2, 0.7, 1.2, 1.2, 1.5], caption="Table 3.1: Multi-Region Datacenter Specifications")

    # Chapter 4
    add_h1(doc, "4. Implementation & Engineering Architecture")
    add_h2(doc, "4.1 Implementation Status & Testing")
    add_p(
        doc,
        "The software architecture comprises six packages: sim/ (simulation objects), schedulers/ (decision policies), "
        "data/ (trace scrapers and workload generators), experiments/ (evaluation suites and plot generators), interactive_dashboard/ "
        "(web UI), and tests/ (verification suite). The automated test suite contains 51 unit and integration tests, all passing, "
        "verifying that zero-slack jobs are never deferred, deadlines are never violated, budgets are strictly enforced, and energy models "
        "satisfy conservation of energy."
    )

    # Table 4.1 Implementation Status
    headers_41s = ["Functional Area", "Interim Status (Review 2)", "Final Status (Review 3)"]
    rows_41s = [
        ["Multi-Region Cloud Simulation", "Functional", "Complete: Queuing, deferral, re-planning, PUE, idle power"],
        ["Workload Representation", "Functional", "Complete: 3 classes, size-proportional budgets, data residency"],
        ["Spatial / Temporal Shifting", "Demonstrated", "Complete: Joint optimization, forecast-aware, hourly re-planning"],
        ["Multi-Objective Decision Engine", "Preliminary", "Complete: Weighted sum & Pareto knee modes, convex SLA risk"],
        ["Historical Carbon Trace Pipeline", "Pending", "Complete: 6 regions x 2 seasons x 672 hourly data points"],
        ["Forecast Uncertainty Modeling", "Pending", "Complete: Calibrated AR(1) error model, 0%–50% sensitivity sweep"],
        ["Large-Scale Multi-Seed Validation", "Pending", "Complete: 20 seeds x 2 seasons x 300 jobs; scaled to 5,000 jobs"],
        ["Pareto Frontier & Hypervolume", "Pending", "Complete: 66-point simplex sweep, hypervolume calculation"],
        ["Real Trace Replay & WAN Staging", "Not Started", "Complete: Alibaba 2018 trace (45k jobs), data transfer model"],
        ["Interactive Cloud Operations UI", "Not Started", "Complete: Real-time dashboard, live Gantt chart, sparklines"],
        ["Automated Test Suite", "Partial", "Complete: 51 unit & integration tests, all passing"]
    ]
    add_table(doc, headers_41s, rows_41s, col_widths=[2.2, 1.8, 3.0], caption="Table 4.1: Implementation Status Across Development Milestones")

    # Chapter 5
    add_h1(doc, "5. Experimental Evaluation & Results")
    add_h2(doc, "5.1 Evaluation Methodology")
    add_p(
        doc,
        "Except where noted, experiments execute 300 heterogeneous jobs on the three core regions (India, Germany, Norway; 16 vCPU each) "
        "with a 12-hour maximum deferral window W, under realistic forecast uncertainty (epsilon = 0.15). Configurations run across both "
        "Winter (January 2024) and Summer (July 2024) historical traces. Experiment E1 uses 20 random seeds (0–19), producing 40 paired "
        "runs per policy. GreenOps hyperparameters were tuned on separate seeds (100–104) to avoid data snooping. Statistical significance "
        "is established using two-sided paired permutation tests with 20,000 permutations."
    )

    add_h2(doc, "5.2 Experiment E1: Main Comparative Benchmark")
    add_p(
        doc,
        "Table 5.1 and Figure 5.1 present the primary comparative results pooled across both seasons (40 paired runs per policy)."
    )

    # Table 5.1 Main Results
    headers_51 = ["Scheduler Policy", "Carbon (kg)", "Delta vs RR", "Delta vs Greenest", "Cost ($)", "Cost vs Cost-Only", "SLA Viol./Run", "Avg / p95 Latency (h)"]
    rows_51 = [
        ["Cost Only", "119.6 ± 8.9", "+22.2%", "+58.2%", "384", "0.0%", "0.15", "3.27 / 6.0"],
        ["Round Robin", "98.1 ± 9.0", "0.0%", "+29.4%", "417", "+8.4%", "0.15", "3.25 / 6.0"],
        ["Greenest Region", "76.0 ± 8.3", "-22.6%", "0.0%", "452", "+17.6%", "0.20", "3.23 / 6.0"],
        ["Temporal Green", "71.1 ± 9.3", "-27.7%", "-6.6%", "454", "+18.1%", "2.80", "6.34 / 15.0"],
        ["GreenOps (Spatial Only)", "76.4 ± 8.3", "-22.2%", "+0.6%", "450", "+17.2%", "0.20", "3.23 / 6.0"],
        ["GreenOps Pareto Knee", "79.6 ± 9.0", "-19.0%", "+4.7%", "434", "+13.0%", "3.05", "4.86 / 12.8"],
        ["GreenOps MOO (Weighted)", "72.0 ± 8.9", "-26.8%", "-5.4%", "455", "+18.3%", "0.28", "3.67 / 7.3"]
    ]
    add_table(doc, headers_51, rows_51, highlight_idx=6, caption="Table 5.1: Main Benchmark Results Pooled Over Both Seasons (40 Paired Runs)")

    # Embed Fig 2
    fig2_path = "results/figures/fig2_main_comparison.png"
    add_image(doc, fig2_path, caption="Figure 5.1: Comparison of Carbon Emissions, Cost, Tail Latency, and SLA Violations", width_in=5.8)

    add_h3(doc, "Key Quantitative Findings from Experiment E1:")
    add_bullet(
        doc,
        "Optimizing purely for financial cost yields the worst environmental outcome: Cost-Only emits 119.6 kg CO2eq (+58.2% vs Greenest Region) "
        "because it concentrates execution in coal-dominated India.",
        bold_prefix="1. Catastrophic Cost-Greedy Emissions: "
    )
    add_bullet(
        doc,
        "Greedy spatial shifting (Greenest Region) cuts emissions by 22.6% relative to Round Robin, demonstrating that routing to hydro-rich "
        "Norway accounts for the majority of available baseline reductions.",
        bold_prefix="2. Spatial Shifting Dominance: "
    )
    add_bullet(
        doc,
        "GreenOps delivers a statistically significant additional 5.3% reduction beyond Greenest Region (paired delta -4.0 kg, p < 0.001) "
        "for a negligible 0.65% cost delta. This gain is larger in summer (-6.7%) when German solar swings are deeper. Its spatial-only ablation "
        "achieves no gain over Greenest Region, proving this advantage originates entirely from intelligent temporal shifting.",
        bold_prefix="3. Statistically Significant Spatio-Temporal Advantage: "
    )
    add_bullet(
        doc,
        "While Temporal Green emits 1.2% less carbon than GreenOps, it defers 48% of workloads (mean wait 3.1 h) versus GreenOps' 16% (mean wait 0.47 h). "
        "Consequently, Temporal Green produces 10x more SLA violations (2.80 vs 0.28 per run, p < 0.001) and doubles p95 tail latency (15.0 h vs 7.3 h). "
        "GreenOps' SLA violations do not differ significantly from carbon-blind Round Robin (p = 0.28).",
        bold_prefix="4. Pristine SLA Compliance & Tail Latency Control: "
    )

    add_h2(doc, "5.3 Latency Distribution & Regional Allocation")
    add_p(
        doc,
        "Figures 5.2 and 5.3 examine queueing latency CDFs and regional allocation shares. Strict real-time jobs achieve identical mean "
        "latency (2.0 h) across all schedulers, confirming that GreenOps never defers urgent workloads. Norway represents the binding "
        "hardware bottleneck, capturing 50%–60% of all CPU-hours under carbon-aware policies."
    )

    # Embed Fig 7 & Fig 8
    fig7_path = "results/figures/fig7_latency_cdf.png"
    add_image(doc, fig7_path, caption="Figure 5.2: Empirical Cumulative Distribution Functions (CDF) of Job Latencies", width_in=5.4)

    fig8_path = "results/figures/fig8_region_share.png"
    add_image(doc, fig8_path, caption="Figure 5.3: Regional Allocation Shares of CPU-Hours Across Core Cloud Regions", width_in=5.0)

    add_h2(doc, "5.4 Experiment E2: Pareto Frontier and Hypervolume Analysis")
    add_p(
        doc,
        "Sweeping objective weights over a 66-point simplex grid traces the continuous trade-off curve between carbon emissions and monetary cost "
        "(Figure 5.4). GreenOps spans a smooth continuum from cost-optimal ($367, 130 kg) to carbon-optimal ($455, 68 kg). All four baselines "
        "lie strictly interior to this frontier. In 2D normalized hypervolume (reference point 1.1), GreenOps Pareto achieves 0.754 and GreenOps "
        "weighted achieves 0.737, vastly exceeding all baselines combined (0.524)."
    )

    # Embed Fig 3
    fig3_path = "results/figures/fig3_pareto_frontier.png"
    add_image(doc, fig3_path, caption="Figure 5.4: Empirical Carbon vs Cost Pareto Frontier Across 66 Simplex Weight Vectors", width_in=5.4)

    add_h2(doc, "5.5 Experiment E3: Robustness to Carbon Forecast Uncertainty")
    add_p(
        doc,
        "Figure 5.5 plots carbon emissions and SLA violations as day-ahead forecast error epsilon scales from 0% to 50%. While Temporal Green "
        "degrades sharply (+4.9% carbon, SLA violations climbing from 2.0 to 3.6), GreenOps degrades by only 1.9%. At error levels above 30%, "
        "GreenOps emits less carbon than Temporal Green while maintaining 85% fewer SLA violations. Dynamic rolling hourly re-planning is "
        "the decisive factor: near-term forecasts become highly accurate, allowing GreenOps to correct mistaken deferrals before deadlines bind."
    )

    # Embed Fig 4
    fig4_path = "results/figures/fig4_forecast_sensitivity.png"
    add_image(doc, fig4_path, caption="Figure 5.5: Sensitivity of Schedulers to Carbon Forecast Uncertainty (0% to 50% Error)", width_in=5.6)

    add_h2(doc, "5.6 Experiment E4: Saturation of Temporal Flexibility")
    add_p(
        doc,
        "Figure 5.6 characterizes the effect of the maximum deferral window W. In the multi-region environment, GreenOps captures 95% of its "
        "maximum temporal carbon reduction within a small 2-hour window (74.6 kg -> 70.2 kg). Extending W beyond 4 hours yields diminishing "
        "returns while inflating tail latency. When spatial shifting is barred (Germany-only pinned workload), longer windows provide larger "
        "gains, capturing 85% of benefit within 4 hours."
    )

    # Embed Fig 5
    fig5_path = "results/figures/fig5_max_wait.png"
    add_image(doc, fig5_path, caption="Figure 5.6: Impact of Maximum Permissible Deferral Window W on Carbon and Latency", width_in=5.6)

    add_h2(doc, "5.7 Experiment E5: Scalability Under Workload Load Stress")
    add_p(
        doc,
        "Figure 5.7 illustrates scheduler behavior as arrival rates scale from 0.5x to 3.0x baseline load. At low load (0.5x), clean capacity "
        "in Norway is abundant, rendering greedy greening nearly optimal (GreenOps delta -2.8%). As load increases and Norway saturates, "
        "GreenOps' advantage over Greenest Region expands to -9.8% at 2x load and -9.6% at 3x load, while Temporal Green suffers 15.5 to 39.7 "
        "SLA violations per run due to catastrophic queueing avalanches."
    )

    # Embed Fig 6
    fig6_path = "results/figures/fig6_load.png"
    add_image(doc, fig6_path, caption="Figure 5.7: Scheduler Performance Under Escalating Arrival Rates (0.5x to 3.0x Load)", width_in=5.6)

    add_h2(doc, "5.8 Experiment E6: Extended Six-Region Scenario")
    add_p(
        doc,
        "Expanding the infrastructure to six heterogeneous regions (India, Germany, Norway, France, Poland, Great Britain) under 2x load "
        "(Table 5.2) increases GreenOps' advantage over Greenest Region to 6.6%, while simultaneously achieving a lower compute cost ($456 vs $462). "
        "GreenOps intelligently routes jobs to low-carbon, cost-effective France (43% share) instead of expensive Norway (6% share)."
    )

    # Table 5.2 Six Region
    headers_52r = ["Scheduler Policy", "Carbon (kg)", "Delta vs Greenest", "Cost ($)", "SLA Viol./Run", "p95 Latency (h)", "Regional Share (FR / NO / GB)"]
    rows_52r = [
        ["Cost Only", "117.1", "+106.7%", "383", "0.0", "6.0", "5% / 4% / 4%"],
        ["Round Robin", "86.9", "+53.4%", "426", "0.1", "6.0", "12% / 8% / 11%"],
        ["Greenest Region", "56.7", "0.0%", "462", "0.1", "6.0", "30% / 16% / 7%"],
        ["Temporal Green", "52.3", "-7.7%", "463", "2.0", "15.1", "32% / 17% / 6%"],
        ["GreenOps MOO", "52.9", "-6.6%", "456", "0.4", "8.3", "43% / 6% / 5%"]
    ]
    add_table(doc, headers_52r, rows_52r, highlight_idx=4, caption="Table 5.2: Extended Six-Region Scenario Under 2x Arrival Load")

    add_h2(doc, "5.9 Experiment E7: Algorithmic Runtime Complexity")
    add_p(
        doc,
        "Table 5.3 documents the wall-clock execution latency per scheduling decision on a single CPU core. GreenOps evaluates candidates "
        "in 0.07 to 0.12 milliseconds, growing strictly linearly with job volume. This negligible overhead confirms suitability for online deployment."
    )

    # Table 5.3 Scalability
    headers_53s = ["Workload Volume", "Greenest Region", "Temporal Green", "GreenOps MOO", "GreenOps Pareto"]
    rows_53s = [
        ["100 Jobs", "0.006 s", "0.011 s", "0.016 s", "0.024 s"],
        ["1,000 Jobs", "0.020 s", "0.059 s", "0.115 s", "0.280 s"],
        ["5,000 Jobs", "0.104 s", "0.279 s", "0.444 s", "1.517 s"],
        ["Latency per Decision", "0.02–0.06 ms", "0.04–0.08 ms", "0.07–0.12 ms", "0.12–0.14 ms"]
    ]
    add_table(doc, headers_53s, rows_53s, col_widths=[1.6, 1.3, 1.3, 1.3, 1.3], caption="Table 5.3: Simulation Wall-Clock Time and Per-Decision Algorithmic Latency")

    add_h2(doc, "5.10 Real Alibaba 2018 Cluster Trace Replay")
    add_p(
        doc,
        "To eliminate threats to validity from synthetic workloads, we replayed a 10% sample (~45,000 jobs per run) of the Alibaba cluster trace "
        "v2018 across three regions of 1,280 vCPU each (Table 5.4). This benchmark incorporates wide-area network (WAN) data-transfer costs "
        "(0.005 kWh/GB, $0.02/GB egress fee, 1 Gbit/s bandwidth) and benchmarks against published literature baselines (Wait Awhile and Online Threshold)."
    )

    # Table 5.4 Alibaba Trace
    headers_54a = ["Scheduler Policy", "Carbon (t)", "Delta vs Greenest", "Total SLA Viol. Rate", "Strict Jobs Late", "p95 Latency (h)", "Jobs Relocated"]
    rows_54a = [
        ["Cost Only", "8.14", "+44.2%", "1.64%", "5.40%", "1.1", "35%"],
        ["Round Robin", "7.26", "+28.4%", "1.67%", "5.51%", "1.1", "34%"],
        ["Greenest Region", "5.66", "0.0%", "1.64%", "5.41%", "1.1", "26%"],
        ["Wait Awhile (Wiesner '21)", "6.18", "+9.2%", "3.15%", "0.28%", "18.9", "0%"],
        ["Temporal Green", "6.08", "+7.5%", "2.65%", "0.23%", "18.3", "29%"],
        ["Online Threshold (Lechowicz '24)", "5.14", "-9.2%", "3.80%", "0.10%", "13.7", "24%"],
        ["GreenOps (Transfer-Unaware)", "5.31", "-6.3%", "0.83%", "0.34%", "12.7", "40%"],
        ["GreenOps (Full)", "5.49", "-3.0%", "0.50%", "0.05%", "10.9", "21%"]
    ]
    add_table(doc, headers_54a, rows_54a, highlight_idx=7, caption="Table 5.4: Alibaba Trace Replay (~45,000 Jobs/Run, 12 Paired Runs, p < 0.001)")

    add_h3(doc, "Key Findings from Alibaba Trace Replay:")
    add_bullet(
        doc,
        "GreenOps achieves the lowest total SLA violation rate (0.50%) and lowest strict violation rate (0.05%) of all policies, "
        "including carbon-blind baselines, because it smoothly clears capacity during demand bursts.",
        bold_prefix="1. Superior SLA Protection: "
    )
    add_bullet(
        doc,
        "While Online Threshold reaches lower carbon (-9.2%), it causes 7.6x more SLA violations (3.80%), rendering it unviable for production.",
        bold_prefix="2. The Threshold Penalty: "
    )
    add_bullet(
        doc,
        "Temporal-only shifting (Wait Awhile) emits 9.2% more carbon than greedy spatial greening, confirming that spatial shifting remains essential.",
        bold_prefix="3. Spatial Primacy: "
    )

    # Chapter 6
    add_h1(doc, "6. Discussion & Practical Implications")
    add_h2(doc, "6.1 Alignment with the Acun et al. Critique")
    add_p(
        doc,
        "Our empirical results strongly align with the theoretical boundaries described by Acun et al. (EuroSys '24). Spatial shifting "
        "provides the lion's share of available decarbonization (~22%), but is bounded by regional capacity and pricing. Temporal shifting "
        "saturates rapidly within 2 to 4 hours. Pushing deferrals beyond 4 hours primarily inflates tail latency and SLA risk rather than "
        "unlocking meaningful carbon gains. The core virtue of GreenOps is capturing nearly all achievable carbon gains while insulating "
        "operators from latency blowouts and forecast failures."
    )

    add_h2(doc, "6.2 Kubernetes Federation Deployment Architecture")
    add_p(
        doc,
        "GreenOps can be deployed directly into production container environments as a Kubernetes Custom Scheduler Extender. By intercepting "
        "Pod admission events across a KubeFed multi-cluster federation, GreenOps evaluates the cluster's regional carbon intensity and "
        "specifies node affinity or mutation annotations (e.g., scheduling delay timers) without modifying upstream Kubernetes binaries."
    )

    # Chapter 7
    add_h1(doc, "7. Conclusion & Future Roadmap")
    add_p(
        doc,
        "This project successfully developed, validated, and demonstrated GreenOps, a multi-objective cloud orchestration framework that "
        "unifies spatial and temporal demand shifting. Across 40 paired runs on empirical grid data and ~45,000-job cluster traces, GreenOps "
        "consistently eliminated 26.8% of emissions over Round Robin and 5.3% over greedy spatial baselines, while reducing SLA violations "
        "by 90% and outperforming all baselines in Pareto hypervolume."
    )
    add_p(
        doc,
        "Future research will incorporate marginal emission signals (WattTime API), integrate real-time battery energy storage systems (BESS), "
        "and package GreenOps as an open-source Kubernetes Custom Resource Definition (CRD) controller."
    )

    # References
    add_h1(doc, "References")
    refs = [
        "B. Acun, B. Lee, F. Kazhamiaka, K. Maeng, U. Gupta, M. Chakkaravarthy, D. Brooks, and C.-J. Wu, 'On the Limitations of Carbon-Aware Temporal and Spatial Workload Shifting in the Cloud,' in Proceedings of the Nineteenth European Conference on Computer Systems (EuroSys '24), pp. 924–941, 2024.",
        "P. Wiesner, I. Behnke, D. Scheinert, K. Gontarska, and L. Thamsen, 'Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud,' in Proceedings of the 22nd International Middleware Conference (Middleware '21), pp. 260–272, 2021.",
        "A. Radovanović et al., 'Carbon-Aware Computing for Datacenters,' IEEE Transactions on Power Systems, vol. 38, no. 2, pp. 1270–1280, 2023.",
        "A. Lechowicz et al., 'Learning-Augmented Competitive Algorithms for Spatiotemporal Online Allocation with Deadline Constraints,' in Proceedings of ACM SIGMETRICS, 2024.",
        "T. Sukprasert, A. Souza, N. Bashir, D. Irwin, and P. Shenoy, 'Spatio-Temporal Shifting to Reduce Carbon, Water, and Land-Use Footprints of Cloud Workloads,' arXiv:2512.08725, 2025.",
        "V. Gsteiger, P. H. Long, Y. Sun, P. Javanrood, and M. Shahrad, 'Caribou: Fine-Grained Geospatial Shifting of Serverless Applications for Sustainability,' in Proceedings of the 30th ACM Symposium on Operating Systems Principles (SOSP '24), pp. 403–420, 2024.",
        "W. A. Hanafy, Q. Liang, N. Bashir, D. Irwin, and P. Shenoy, 'CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency,' Proc. ACM Meas. Anal. Comput. Syst., vol. 7, no. 3, 2023.",
        "Z. Zhou et al., 'Carbon-Aware Load Balancing for Geo-Distributed Cloud Services,' in IEEE MASCOTS, 2013.",
        "M. Chadha et al., 'GreenCourier: Carbon-Aware Scheduling for Serverless Functions,' in WoSC '23, pp. 18–23, 2023.",
        "A. Souza et al., 'Ecovisor: A Virtual Energy System for Carbon-Efficient Applications,' in ASPLOS '23, pp. 252–265, 2023."
    ]
    for r in refs:
        add_bullet(doc, r)

    # Appendix
    add_h1(doc, "Appendix: Step-by-Step Reproduction Guide")
    add_p(
        doc,
        "To reproduce all experimental results, figures, benchmarks, and interactive dashboards, execute the following commands:",
        bold_prefix="Reproduction Commands: "
    )
    add_bullet(doc, ".\\greenops_env\\Scripts\\Activate.ps1", bold_prefix="1. Activate Environment: ")
    add_bullet(doc, "python -m unittest discover -s tests -v (Executes all 51 automated unit and integration tests)", bold_prefix="2. Run Unit Test Suite: ")
    add_bullet(doc, "python demo.py (Executes interactive 5-step terminal viva demonstration)", bold_prefix="3. Run Viva Demo: ")
    add_bullet(doc, "python interactive_dashboard\\server.py (Launches real-time browser dashboard at http://localhost:8050)", bold_prefix="4. Launch Web Dashboard: ")
    add_bullet(doc, "python -m experiments.comparison.run_all (Executes 5-job benchmark in Table 4.1)", bold_prefix="5. Execute Benchmark: ")
    add_bullet(doc, "python -m experiments.evaluation (Runs complete E1–E7 evaluation suites into results/evaluation/*.csv)", bold_prefix="6. Run Evaluation Suite: ")
    add_bullet(doc, "python -m experiments.plots (Renders publication-grade figures into results/figures/*.png)", bold_prefix="7. Generate Figures: ")

    # Output paths
    docx_path = os.path.abspath("GreenOps_Review_3_Report.docx")
    pdf_path = os.path.abspath("GreenOps_Review_3_Report.pdf")
    save_and_convert(doc, docx_path, pdf_path)

if __name__ == "__main__":
    build_review_3()
