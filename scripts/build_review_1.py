"""
build_review_1.py
Generates the Project Review 1 Report:
Focus: Problem Statement, How We Solve It, Conceptual Architecture Blueprint, Literature Survey & Methodology.
NOTE: Per user instructions, greenops_architecture.png is NOT embedded in this Review 1 document.
"""

import os
from docx.shared import Inches, Pt, RGBColor
from report_builder import (
    create_base_doc, add_cover_page, add_h1, add_h2, add_h3,
    add_p, add_bullet, add_table, save_and_convert
)

def build_review_1():
    doc = create_base_doc("GreenOps Cloud Orchestration — Review 1 Report")

    # Cover Page
    add_cover_page(
        doc,
        review_num="1",
        review_stage_title="Review 1",
        review_sub="Problem Statement, Solution Methodology & Conceptual Architecture Blueprint"
    )

    # Executive Summary / Abstract
    add_h1(doc, "Executive Summary")
    add_p(
        doc,
        "Cloud data centres represent one of the fastest-growing consumers of electrical power worldwide, currently accounting "
        "for approximately 1% to 2% of global electricity consumption. Despite rapid advancements in cloud orchestration, traditional "
        "cluster schedulers—such as Kubernetes bin-packers, HPC batch allocators, and public cloud autoscalers—remain strictly "
        "carbon-blind. They optimize allocations for execution turnaround, hardware utilization, and financial cost, operating under "
        "the flawed assumption that electricity has a static and uniform environmental impact."
    )
    add_p(
        doc,
        "In reality, the carbon intensity of electricity (measured in gCO2eq/kWh) varies drastically across both geographical space "
        "and diurnal time. For instance, grids dominated by hydropower (such as Norway) operate at baseline intensities below "
        "30 gCO2eq/kWh, while fossil-heavy grids (such as Poland and coal-based regions of India) consistently exceed 600 gCO2eq/kWh. "
        "Furthermore, grids with substantial solar and wind penetration (such as Germany and Great Britain) exhibit severe intra-day "
        "volatility, where carbon intensity can swing by more than 300 gCO2eq/kWh within a single 24-hour cycle. Consequently, identical "
        "computational workloads can produce vastly different carbon emissions depending purely on where and when they are executed."
    )
    add_p(
        doc,
        "This project proposes GreenOps, a multi-objective carbon-aware cloud orchestration system designed for geo-distributed cloud "
        "infrastructures. GreenOps unifies spatial demand shifting (routing workloads to cleaner geographic regions) with forecast-aware "
        "temporal demand shifting (deferring delay-tolerant batch computations to cleaner hours). This Review 1 report formalizes the "
        "core problem statement, details our solution methodology, defines the mathematical multi-objective optimization framework, "
        "presents the modular system architecture, and provides a comparative literature review highlighting existing research gaps."
    )

    # Section 1
    add_h1(doc, "1. Problem Motivation and Context")
    add_h2(doc, "1.1 The Environmental Footprint of Modern Cloud Computing")
    add_p(
        doc,
        "The exponential expansion of digital services, large-scale artificial intelligence (AI) model training and inference, "
        "big-data analytics pipelines, and enterprise cloud migrations has led to surging energy demands in hyper-scale datacenters. "
        "Datacenters globally consume upwards of 240–340 TWh annually. While cloud providers have made voluntary commitments toward "
        "net-zero emissions through renewable energy certificates (RECs) and power purchase agreements (PPAs), these accounting "
        "mechanisms do not eliminate physical grid emissions occurring in real time."
    )
    add_p(
        doc,
        "True physical decarbonization requires operational carbon awareness: aligning computational workloads with the real-time "
        "availability of low-carbon electricity on the physical grid powering each datacenter. If a computational job executes during "
        "hours when fossil-fuel peaking plants are ramped up, the marginal carbon emissions of that job are directly emitted into "
        "the atmosphere, regardless of annual offsetting credits."
    )

    add_h2(doc, "1.2 Dual Dimensions of Carbon Variability")
    add_p(
        doc,
        "Carbon-aware orchestration exploits two fundamental dimensions of electrical grid physics:",
        bold_prefix="Grid Physics Realities: "
    )
    add_bullet(
        doc,
        "Significant baseload disparities exist across regional electrical interconnects. Countries with extensive nuclear or "
        "hydroelectric baseloads (e.g., France, Norway) exhibit perpetually low carbon intensities (20–50 gCO2eq/kWh). Conversely, "
        "regions reliant on thermal coal or lignite generation (e.g., Poland, northern India) exhibit baseline intensities exceeding "
        "550–750 gCO2eq/kWh. Workloads that can be moved geographically without regulatory or data-gravity penalties can achieve "
        "up to a 90% emissions reduction through spatial relocation.",
        bold_prefix="Spatial Heterogeneity: "
    )
    add_bullet(
        doc,
        "In grids with high penetration of variable renewable energy (VRE)—predominantly solar photovoltaics and wind turbines—carbon "
        "intensity fluctuates dynamically hour-by-hour. Solar generation produces a predictable midday trough in carbon intensity, "
        "while wind generation introduces multi-hour low-carbon surges that often do not coincide with peak commercial demand. In Germany, "
        "for example, carbon intensity regularly fluctuates between 130 gCO2eq/kWh during windy afternoons and 650 gCO2eq/kWh during "
        "still, cold winter evenings. Flexible workloads that tolerate deferral can exploit these valleys through temporal shifting.",
        bold_prefix="Temporal Volatility: "
    )

    # Section 2
    add_h1(doc, "2. Problem Statement and Research Challenges")
    add_h2(doc, "2.1 Shortcomings of Existing Cloud Schedulers")
    add_p(
        doc,
        "Current cloud orchestration frameworks suffer from critical structural blind spots:",
        bold_prefix="The Status Quo: "
    )
    add_bullet(
        doc,
        "Mainstream container orchestrators (such as the default Kubernetes kube-scheduler) prioritize node resource packing, "
        "spreading pods across failure domains, and optimizing network locality. Carbon intensity is completely omitted from the "
        "scheduling scoring function.",
        bold_prefix="Carbon Blindness: "
    )
    add_bullet(
        doc,
        "Existing academic prototypes that do consider carbon often pursue carbon minimization in isolation. They naively route all "
        "traffic to the currently greenest region or delay jobs indefinitely until renewable generation peaks. This approach leads to "
        "catastrophic Service Level Agreement (SLA) violations, extreme queueing delays, and severe financial budget overruns.",
        bold_prefix="Isolated Optimization & SLA Degradation: "
    )
    add_bullet(
        doc,
        "Most prior literature operates under the unrealistic assumption of perfect carbon foresight. In practice, day-ahead and "
        "intra-day grid carbon forecasts exhibit significant error that escalates with the forecast horizon. Schedulers that trust "
        "imperfect forecasts blindly frequently defer jobs into forecast 'green valleys' that fail to materialize, ultimately forcing "
        "execution during dirty emergency peaking hours.",
        bold_prefix="Unrealistic Perfect Foresight Assumptions: "
    )

    add_h2(doc, "2.2 The Multi-Objective Trilemma")
    add_p(
        doc,
        "The core research challenge is balancing three competing forces under strict enterprise constraints:",
        bold_prefix="Formal Problem Definition: "
    )
    add_p(
        doc,
        "Given a heterogeneous stream of incoming cloud workloads with distinct arrival times, CPU/memory demands, execution runtimes, "
        "firm deadlines, cost budgets, and data residency restrictions, how can an orchestrator jointly determine the optimal execution "
        "region and start time such that carbon emissions are minimized, financial compute costs are controlled, and SLA deadline "
        "compliance is guaranteed, even under substantial carbon forecast uncertainty?"
    )

    # Section 3
    add_h1(doc, "3. Proposed Solution: How GreenOps Solves It")
    add_p(
        doc,
        "GreenOps addresses this challenge through a principled, multi-objective spatio-temporal scheduling engine designed with "
        "hard constraint verification, convex SLA risk modeling, confidence gating, and dynamic rolling re-planning."
    )

    add_h2(doc, "3.1 Joint Spatio-Temporal Search Space")
    add_p(
        doc,
        "Unlike decoupled architectures that first select a region and subsequently decide when to execute, GreenOps treats scheduling "
        "as a joint optimization problem over candidate pairs x = (r, s), where r represents an eligible cloud region and s represents "
        "a candidate start time within the job's permissible deferral window W. For an incoming job j arriving at time t, the candidate "
        "search space X_j(t) is defined as:"
    )
    add_p(
        doc,
        "X_j(t) = { (r, s) : r in A_j,  Cost_r(j) <= B_j,  s in {t, ceil(t), ..., min(t+W, L_j)},  (s = t => Region r has free capacity) }",
        italic=True
    )
    add_p(
        doc,
        "Here, A_j denotes the subset of geographically permissible regions (enforcing data sovereignty and residency laws), B_j is the "
        "job's maximum budgetary ceiling, and L_j = D_j - d_j represents the latest permissible start time to guarantee completion "
        "before deadline D_j with runtime d_j."
    )

    add_h2(doc, "3.2 Mathematical Formulation of Objectives")
    add_p(
        doc,
        "Every feasible candidate pair x = (r, s) is evaluated against three normalized objective functions:",
        bold_prefix="Tri-Objective Scoring: "
    )
    add_bullet(
        doc,
        "Calculated as the total electrical energy consumed by the job in region r multiplied by the forecast carbon intensity over "
        "the execution window [s, s + d_j], adjusted by a forecast error confidence penalty: C(x) = E_r(j) * CI_forecast(r, s, s+d_j) * (1 + kappa * sigma(s - t)). "
        "The parameter kappa acts as a confidence gate, penalizing distant, uncertain forecasts.",
        bold_prefix="1. Carbon Emissions Objective C(x): "
    )
    add_bullet(
        doc,
        "Calculated from the allocated virtual CPUs, execution duration, and regional unit resource pricing: K(x) = cpu_j * d_j * Price_r.",
        bold_prefix="2. Monetary Compute Cost Objective K(x): "
    )
    add_bullet(
        doc,
        "Modeled as a strictly convex penalty on consumed deadline slack: R(x) = ((s - t) / (L_j - t))^2. This quadratic penalty ensures "
        "that deferral is inexpensive when ample slack remains, but becomes prohibitively expensive as the candidate start time approaches "
        "the latest start time L_j, preventing eleventh-hour SLA violations.",
        bold_prefix="3. Convex SLA Risk Objective R(x): "
    )

    add_h2(doc, "3.3 Normalization and Selection Modes")
    add_p(
        doc,
        "GreenOps implements two complementary decision modes to accommodate different operational preferences:",
        bold_prefix="Dual Operational Modes: "
    )
    add_bullet(
        doc,
        "Score(x) = w_c * p_j * (C(x) / C_max) + w_k * (K(x) / K_max) + w_r * R(x), subject to w_c + w_k + w_r = 1. Ratio-to-max "
        "normalization preserves true relative differences without distorting minute variations. Here, p_j represents an optional "
        "per-job carbon priority weighting.",
        bold_prefix="Weighted Sum Mode: "
    )
    add_bullet(
        doc,
        "Filters the candidate set down to the Pareto-optimal non-dominated frontier in 3D objective space (Carbon, Cost, SLA Risk). "
        "It then selects the optimal knee solution using the weighted Tchebycheff distance metric to the utopian ideal point. This allows "
        "GreenOps to explore non-convex regions of the Pareto trade-off surface.",
        bold_prefix="Pareto Knee Mode: "
    )

    add_h2(doc, "3.4 Rolling Hourly Re-Planning Under Forecast Uncertainty")
    add_p(
        doc,
        "A critical innovation of GreenOps is its dynamic rolling re-planning loop. If the chosen candidate dictates deferring execution "
        "by more than one hour, the job is not statically frozen. Instead, the job wakes up every elapsed hour to query a refreshed, "
        "lower-horizon carbon forecast and re-evaluate its scheduling decision. If renewable conditions improve or deteriorate, GreenOps "
        "adaptively revises its placement before commitments become binding."
    )

    # Section 4
    add_h1(doc, "4. System Architecture Blueprint")
    add_p(
        doc,
        "The GreenOps architecture is constructed as a modular, discrete-event cloud simulation framework designed for rigorous "
        "experimentation, multi-seed validation, and real-time dashboard observability. The blueprint comprises six foundational subsystems:"
    )

    add_h2(doc, "4.1 Architectural Subsystems")
    add_bullet(
        doc,
        "Generates realistic, heterogeneous cloud jobs characterized by synthetic or trace-derived arrival times, execution runtimes, "
        "resource footprints (CPU/memory), deadlines, flexibility classes, budgets, and allowed geographic zones.",
        bold_prefix="1. Workload Source & Characterization: "
    )
    add_bullet(
        doc,
        "Simulates geo-distributed datacenter infrastructure across multiple international regions (India, Germany, Norway, France, "
        "Poland, Great Britain). Enforces physical vCPU and memory resource capacities, regional power utilization curves (idle vs peak kW), "
        "regional Power Usage Effectiveness (PUE) multipliers, and monetary compute rates.",
        bold_prefix="2. Multi-Region Distributed Cloud Engine: "
    )
    add_bullet(
        doc,
        "Ingests multi-week real-world historical grid generation data from the Energy-Charts API (Fraunhofer ISE) and National Grid ESO. "
        "Synthesizes horizon-dependent, autocorrelated AR(1) forecast error calibrated to empirical transmission operator benchmarks.",
        bold_prefix="3. Carbon Forecaster & Trace Pipeline: "
    )
    add_bullet(
        doc,
        "The algorithmic core that validates hard constraints, enumerates (region x start-time) candidates, evaluates multi-objective "
        "trade-offs, and issues dispatch or deferral directives.",
        bold_prefix="4. Multi-Objective Decision Engine: "
    )
    add_bullet(
        doc,
        "Manages discrete-event queuing, allocation, execution, and release using SimPy. Computes actual energy consumption using the "
        "regional power model and applies time-weighted carbon intensity across the entire duration of each job.",
        bold_prefix="5. Execution & Dispatch Engine: "
    )
    add_bullet(
        doc,
        "Tracks complete telemetry including job completions, SLA violations, tardiness, financial cost, total carbon emissions, "
        "regional utilization shares, and statistical confidence intervals.",
        bold_prefix="6. Metrics & Verification Subsystem: "
    )

    # Table 4.1
    add_h2(doc, "4.2 Subsystem Interface Specification")
    headers_41 = ["Subsystem Name", "Primary Inputs", "Primary Outputs", "Key Functionality"]
    rows_41 = [
        ["Workload Generator", "Job distributions, arrival rates, seed", "Stream of Job objects with SLA tags", "Classifies workloads into Strict, Batch, and Flexible tiers"],
        ["Carbon Forecaster", "Historical trace DB, simulation time t, horizon h", "Forecast carbon intensity with error sigma(h)", "Emulates real grid APIs with AR(1) autocorrelated error noise"],
        ["Constraint Filter", "Job constraints, regional capacities", "Feasible candidate subset X_j(t)", "Enforces data residency, capacity checks, and budget ceilings"],
        ["Decision Engine", "Feasible candidates, weight vectors", "Optimal candidate x* = (r*, s*)", "Evaluates weighted sum or Pareto Tchebycheff knee metric"],
        ["Dispatch & Re-planner", "Optimal candidate, current time t", "Immediate execution or sleep timer", "Dispatches immediately or re-plans hourly as forecast improves"],
        ["Execution Engine", "Dispatched jobs, regional hardware", "Resource allocation, release events", "Calculates regional idle/dynamic energy and actual emissions"],
        ["Metrics Collector", "Completed & rejected job logs", "Carbon, cost, SLA stats, Pareto HV", "Aggregates 40 paired simulation runs and permutation tests"]
    ]
    add_table(doc, headers_41, rows_41, col_widths=[1.5, 1.7, 1.6, 2.0], caption="Table 4.1: Subsystem Interface and Contract Specifications")

    # Section 5
    add_h1(doc, "5. Literature Review and Research Gaps")
    add_h2(doc, "5.1 Survey of Related Literature")
    add_p(
        doc,
        "Carbon-aware cloud computing has gained significant momentum across academia and industry over the past five years. "
        "Our survey synthesizes twenty influential papers spanning eight foundational research threads:",
        bold_prefix="Academic Landscape: "
    )
    add_bullet(
        doc,
        "Pioneering research by Wiesner et al. (Let's Wait Awhile, Middleware '21) demonstrated that deferring delay-tolerant jobs "
        "to periods of peak renewable generation within a single datacenter can reduce operational emissions by 15–30%. However, "
        "their approach did not support spatial shifting and was vulnerable to forecast errors.",
        bold_prefix="Temporal Shifting: "
    )
    add_bullet(
        doc,
        "Early systems by Zhou et al. (MASCOTS '13) and recent architectures like Caribou (SOSP '24) and CarbonEdge (HPDC '25) "
        "route serverless functions and web requests to geographically greener datacenters. However, these systems treat workloads "
        "as immediately dispatchable, neglecting temporal deferral opportunities.",
        bold_prefix="Spatial Shifting: "
    )
    add_bullet(
        doc,
        "Google's carbon-aware platform (Radovanović et al., IEEE TPS '23) dynamically shapes non-urgent compute capacity across "
        "global datacenters using day-ahead carbon forecasts. However, it functions as an operational capacity planner rather than an "
        "online job scheduler that respects customer-level monetary budgets and deadlines.",
        bold_prefix="Industrial Grid Shaping: "
    )
    add_bullet(
        doc,
        "Acun et al. (EuroSys '24) published a seminal critical analysis highlighting the practical boundaries of shifting. They proved "
        "that the marginal gains of temporal shifting saturate within a 2–4 hour window, and that spatial shifting is fundamentally "
        "constrained by regional capacity bottlenecks and network latency.",
        bold_prefix="Empirical Limits of Shifting: "
    )

    add_h2(doc, "5.2 Comparative Capability Matrix")
    headers_51 = ["Approach / System", "Spatial", "Temporal", "Cost Aware", "Hard SLA", "Forecast Error", "Multi-Obj."]
    rows_51 = [
        ["Round Robin (K8s Default)", "Spreading", "No", "No", "No", "Ignored", "No"],
        ["Cost-Only Scheduler", "Yes (Cheapest)", "No", "Primary", "No", "Ignored", "No"],
        ["Greenest Region (Greedy Spatial)", "Yes", "No", "No", "No", "Ignored", "No"],
        ["Wait Awhile (Wiesner '21)", "No", "Yes", "Partial", "Partial", "Rarely", "No"],
        ["Temporal Green (Greedy Search)", "No", "Yes", "No", "Violates", "Ignored", "No"],
        ["Google Carbon-Aware ('23)", "Yes", "Yes", "Internal", "Batch only", "Calibrated", "Heuristic"],
        ["Online Threshold (Lechowicz '24)", "Yes", "Yes", "No", "Yes (Online)", "Forecast-free", "Competitive"],
        ["GreenOps (This Project)", "Yes", "Yes", "Yes", "Yes (Hard)", "Modelled + Gated", "Yes (Pareto+Weight)"]
    ]
    add_table(doc, headers_51, rows_51, highlight_idx=7, caption="Table 5.1: Comparative Capability Matrix of Schedulers")

    add_h2(doc, "5.3 Identified Research Gaps")
    headers_52 = ["Identified Research Gap", "Shortcomings in Literature", "GreenOps Proposed Solution"]
    rows_52 = [
        ["Isolated Shifting Dimensions", "Prior works treat spatial and temporal shifting as mutually exclusive mechanisms.", "Joint candidate space (region x start hour) optimized simultaneously under a single decision."],
        ["Lack of Cost & Budget Realism", "Carbon optimizers ignore regional price disparities, causing massive budget blowouts.", "Strict budgetary constraints B_j and normalized cost objectives K(x) integrated directly."],
        ["Catastrophic SLA Violations", "Aggressive green schedulers exhaust deadline slack, doubling tail latencies.", "Convex SLA penalty R(x) and hard deadline feasibility checks guarantee strict timeliness."],
        ["Blind Faith in Forecasts", "Most simulators assume perfect foresight, failing when real weather deviates.", "Calibrated AR(1) error model, confidence gating (kappa*sigma), and hourly rolling re-planning."],
        ["Absence of Pareto Analysis", "Literature is dominated by arbitrary weighted sums without formal trade-off curves.", "Full 66-point simplex sweep tracing continuous Pareto frontiers with hypervolume metrics."]
    ]
    add_table(doc, headers_52, rows_52, col_widths=[1.8, 2.5, 2.5], caption="Table 5.2: Specific Research Gaps and GreenOps Contributions")

    # Section 6
    add_h1(doc, "6. Project Scope, Workload Model & Methodology")
    add_h2(doc, "6.1 Workload Classification")
    add_p(
        doc,
        "GreenOps models realistic enterprise workloads across three distinct operational tiers:",
        bold_prefix="Workload Heterogeneity: "
    )
    add_bullet(
        doc,
        "Represents 40% of incoming jobs. Low runtime (1–3 h), tight deadlines (2–5 h slack), never deferred (W = 0). Evaluated only "
        "for immediate spatial placement to prevent user-facing latency penalties.",
        bold_prefix="1. Strict Real-Time Services (API / Web): "
    )
    add_bullet(
        doc,
        "Represents 35% of incoming jobs. Moderate runtime (2–6 h), moderate slack (5–10 h), flexible deferral allowed. High cost sensitivity.",
        bold_prefix="2. Batch Analytics (ETL / Reporting): "
    )
    add_bullet(
        doc,
        "Represents 25% of incoming jobs. Longer runtimes (2–6 h), generous slack (8–16 h), high carbon priority. Prime candidates for temporal shifting.",
        bold_prefix="3. Flexible Computations (Model Training / Simulation): "
    )

    add_h2(doc, "6.2 Multi-Region Environment Parameters")
    add_p(
        doc,
        "The simulation environment incorporates six diverse cloud regions reflecting actual global infrastructure:",
        bold_prefix="Geographic Diversity: "
    )
    headers_61 = ["Region", "Price ($/vCPU-h)", "Idle / Max Power (kW)", "PUE", "Mean CI Winter", "Mean CI Summer", "Trace Nature"]
    rows_61 = [
        ["India (IN)", "0.08", "0.12 / 0.55", "1.60", "708 g/kWh", "633 g/kWh", "Modelled (CEA Calibrated)"],
        ["Germany (DE)", "0.11", "0.10 / 0.50", "1.30", "353 g/kWh", "331 g/kWh", "Real Energy-Charts Mix"],
        ["Norway (NO)", "0.14", "0.08 / 0.42", "1.15", "28 g/kWh", "31 g/kWh", "Real Energy-Charts Mix"],
        ["France (FR)", "0.12", "0.10 / 0.48", "1.35", "52 g/kWh", "29 g/kWh", "Real Energy-Charts Mix"],
        ["Poland (PL)", "0.09", "0.11 / 0.52", "1.45", "586 g/kWh", "626 g/kWh", "Real Energy-Charts Mix"],
        ["Great Britain (GB)", "0.13", "0.10 / 0.48", "1.35", "159 g/kWh", "113 g/kWh", "Real National Grid ESO API"]
    ]
    add_table(doc, headers_61, rows_61, col_widths=[1.4, 1.0, 1.3, 0.7, 1.1, 1.1, 1.4], caption="Table 6.1: Multi-Region Datacenter Profiles and Physical Parameters")

    # Section 7
    add_h1(doc, "7. Project Roadmap and Milestones")
    headers_71 = ["Milestone", "Target Review", "Deliverables", "Completion Status"]
    rows_71 = [
        ["Problem Formulation & Conceptual Design", "Review 1", "Problem statement, mathematical formulation, literature survey, modular blueprint", "100% Completed"],
        ["Simulation Engine & Baseline Development", "Review 2", "SimPy framework, workload generator, trace pipeline, 4 baseline schedulers", "50%–60% Target"],
        ["Multi-Objective Decision Engine & Bug Fixes", "Review 2", "Weighted scoring, convex SLA risk, confidence gate, 5-job benchmark validation", "50%–60% Target"],
        ["Comprehensive Multi-Seed Evaluation (E1–E7)", "Review 3", "20 seeds x 2 seasons, Pareto hypervolume, forecast error sweep, load stress", "100% Final Target"],
        ["Real Trace Replay & WAN Staging", "Review 3", "Alibaba 2018 cluster replay (45k jobs), WAN network data transfer model", "100% Final Target"],
        ["Interactive Cloud Operations Dashboard", "Review 3", "Live job dispatcher, real-time Gantt timeline, live carbon sparklines, operator UI", "100% Final Target"]
    ]
    add_table(doc, headers_71, rows_71, col_widths=[1.8, 1.0, 2.7, 1.3], caption="Table 7.1: Project Milestone Roadmap Across Evaluation Reviews")

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
        "Z. Zhou et al., 'Carbon-Aware Load Balancing for Geo-Distributed Cloud Services,' in IEEE International Symposium on Modeling, Analysis & Simulation of Computer and Telecommunication Systems (MASCOTS), 2013."
    ]
    for r in refs:
        add_bullet(doc, r)

    # Output paths
    docx_path = os.path.abspath("GreenOps_Review_1_Report.docx")
    pdf_path = os.path.abspath("GreenOps_Review_1_Report.pdf")
    save_and_convert(doc, docx_path, pdf_path)

if __name__ == "__main__":
    build_review_1()
