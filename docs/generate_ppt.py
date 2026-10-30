"""
Generate the Final Comprehensive Project Presentation for GreenOps Cloud Orchestration.
Creates:
  - docs/GreenOps_Final_Presentation.pptx
  - docs/GreenOps_Presentation.pptx (synchronized copy)
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
FIGS_DIR = os.path.join(PROJECT_ROOT, "results", "figures")
ARCH_FIG = os.path.join(DOCS_DIR, "architecture", "greenops_architecture.png")

# Palette
DARK_BG = RGBColor(11, 15, 23)        # #0b0f17
CARD_BG = RGBColor(24, 34, 52)        # #182234
CARD_BORDER = RGBColor(38, 53, 77)    # #26354d
TEXT_WHITE = RGBColor(240, 244, 252)  # #f0f4fc
TEXT_MUTED = RGBColor(148, 163, 184)  # #94a3b8
EMERALD = RGBColor(16, 185, 129)      # #10b981
BLUE = RGBColor(59, 130, 246)         # #3b82f6
AMBER = RGBColor(245, 158, 11)        # #f59e0b
ROSE = RGBColor(244, 63, 94)          # #f43f5e


def set_slide_background(slide, prs):
    """Fill slide with dark navy background."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = DARK_BG
    bg_shape.line.fill.background()
    return bg_shape


def add_header(slide, title_text, category_text="GREENOPS CLOUD ORCHESTRATION"):
    """Standard professional top header."""
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
    tf = header_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = EMERALD

    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE


def add_card(slide, left, top, width, height, title=None, bg_color=CARD_BG, border_color=CARD_BORDER):
    """Draw a styled card container."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)

    if title:
        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE

    return shape


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, prs)

    # Accent decorative banner
    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.15), Inches(3.2))
    banner.fill.solid()
    banner.fill.fore_color.rgb = EMERALD
    banner.line.fill.background()

    tb_title = s1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(11.2), Inches(3.4))
    tf1 = tb_title.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "FINAL PROJECT DEFENSE & PRESENTATION"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = EMERALD

    p1 = tf1.add_paragraph()
    p1.text = "GreenOps Cloud Orchestration"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_before = Pt(8)

    p2 = tf1.add_paragraph()
    p2.text = "Spatial and Temporal Demand Shifting for Carbon-Aware Cloud Workload Scheduling"
    p2.font.size = Pt(16)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(8)

    # Authors Card
    add_card(s1, Inches(0.8), Inches(4.9), Inches(11.733), Inches(1.8))
    tb_auth = s1.shapes.add_textbox(Inches(1.1), Inches(5.05), Inches(11.2), Inches(1.5))
    tfa = tb_auth.text_frame
    tfa.word_wrap = True

    pa1 = tfa.paragraphs[0]
    pa1.text = "PROJECT TEAM MEMBERS:"
    pa1.font.size = Pt(11)
    pa1.font.bold = True
    pa1.font.color.rgb = EMERALD

    pa2 = tfa.add_paragraph()
    pa2.text = "• SANJEEVKUMAR K S (24MID0172)\n• NITHISH KUMAR (24MIC0032)\n• MUHAMMED FAHEEM K (24MID0158)"
    pa2.font.size = Pt(13)
    pa2.font.bold = True
    pa2.font.color.rgb = TEXT_WHITE
    pa2.space_before = Pt(4)

    pa3 = tfa.add_paragraph()
    pa3.text = "School of Information Technology & Engineering · Vellore Institute of Technology, Vellore"
    pa3.font.size = Pt(11.5)
    pa3.font.color.rgb = TEXT_MUTED
    pa3.space_before = Pt(6)

    # =========================================================================
    # SLIDE 2: Background & Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, prs)
    add_header(s2, "Background & The Cloud Carbon Crisis", "1. Problem Context")

    # 3 Stat Cards
    c1 = add_card(s2, Inches(0.8), Inches(1.6), Inches(3.6), Inches(2.2))
    tb = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.2), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "> 20× Variance"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p2 = tf.add_paragraph()
    p2.text = "Grid carbon intensity across regions at the same hour: Norway (28 g/kWh) vs Poland (586 g/kWh) and India (~650 g/kWh)."
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(6)

    c2 = add_card(s2, Inches(4.8), Inches(1.6), Inches(3.6), Inches(2.2))
    tb = s2.shapes.add_textbox(Inches(5.0), Inches(1.8), Inches(3.2), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "130–650 g/kWh"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = BLUE
    p2 = tf.add_paragraph()
    p2.text = "Diurnal swings in Germany within a single day as solar output peaks at midday and drops at dusk. Huge temporal shifting opportunity."
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(6)

    c3 = add_card(s2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(2.2))
    tb = s2.shapes.add_textbox(Inches(9.0), Inches(1.8), Inches(3.3), Inches(1.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "0 Signals"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = ROSE
    p2 = tf.add_paragraph()
    p2.text = "Used by today's default cloud schedulers (Kubernetes default, Slurm, autoscalers). They optimize only for bin packing, latency, and cost."
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(6)

    # Narrative Card Below
    add_card(s2, Inches(0.8), Inches(4.2), Inches(11.7), Inches(2.6), "Why Naive Greening Fails in Practice")
    tb = s2.shapes.add_textbox(Inches(1.1), Inches(4.7), Inches(11.1), Inches(1.9))
    tf = tb.text_frame
    tf.word_wrap = True
    bullets = [
        ("Greedy Spatial Shifting Causes Congestion: ", "Routing all jobs to the cleanest region quickly saturates clean capacity (e.g. Norway), causing long queues and SLA violations."),
        ("Naive Temporal Shifting Causes Massive Deadlines Misses: ", "Delaying jobs to 'cleaner forecast hours' without SLA risk management results in severe deadline violations (up to 10× violations under Temporal Green)."),
        ("Data Gravity & Egress Fees: ", "Moving workloads across regions incurs WAN transfer delays, network energy, and substantial cloud egress pricing ($0.02/GB)."),
        ("Forecast Uncertainty: ", "Grid forecasts are not perfect oracles. Real forecasts suffer 10–20% error that compounds over future horizons.")
    ]
    for idx, (b_title, b_desc) in enumerate(bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        run1 = p.add_run()
        run1.text = "• " + b_title
        run1.font.bold = True
        run1.font.size = Pt(12)
        run1.font.color.rgb = TEXT_WHITE
        run2 = p.add_run()
        run2.text = b_desc
        run2.font.size = Pt(12)
        run2.font.color.rgb = TEXT_MUTED
        if idx > 0: p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 3: Problem Statement & Project Objectives
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, prs)
    add_header(s3, "Problem Statement & Project Objectives", "2. Goals & Scope")

    add_card(s3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2), "The Central Research Question")
    tb = s3.shapes.add_textbox(Inches(1.1), Inches(2.2), Inches(5.0), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Can a cloud scheduler simultaneously exploit spatial and temporal carbon variance without:"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE
    q_bullets = [
        ("Violating SLA Deadlines: ", "Ensuring interactive/strict jobs never wait, and flexible jobs complete on time."),
        ("Blowing Monetary Budgets: ", "Keeping compute and inter-region data egress fees within operator caps."),
        ("Blindly Trusting Flawed Forecasts: ", "Guarding against inaccurate day-ahead carbon forecast signals."),
        ("Ignoring Data Gravity: ", "Accounting for the latency, network energy, and egress costs of migrating large datasets.")
    ]
    for b_title, b_desc in q_bullets:
        p = tf.add_paragraph()
        r1 = p.add_run(); r1.text = "❌ " + b_title; r1.font.bold = True; r1.font.color.rgb = ROSE; r1.font.size = Pt(12)
        r2 = p.add_run(); r2.text = b_desc; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(12)
        p.space_before = Pt(6)

    add_card(s3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2), "Core Project Contributions")
    tb = s3.shapes.add_textbox(Inches(7.1), Inches(2.2), Inches(5.1), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    c_bullets = [
        ("Joint Spatio-Temporal MOO Formulation: ", "A 3-objective optimization balancing carbon, cost, and quadratic SLA risk with hard deadline constraints."),
        ("Confidence-Gated Forecast Uncertainty: ", "Inflates future carbon estimates by horizon uncertainty (κ · σ(h)) and re-plans deferred jobs hourly."),
        ("High-Fidelity Discrete-Event Simulator: ", "SimPy-based multi-region simulator modeling node pools, PUE, idle/dynamic power, and decoupled WAN staging."),
        ("Trace-Driven Industrial Validation: ", "Validated against real 2024 grid data and 45,000 real batch jobs from the Alibaba Cluster Trace v2018."),
        ("Interactive Web Dashboard: ", "A full-featured GUI for real-time workload assignment, live grid sparklines, Gantt timeline, and 7-policy benchmarking.")
    ]
    for idx, (b_title, b_desc) in enumerate(c_bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "✓ " + b_title; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(12)
        r2 = p.add_run(); r2.text = b_desc; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(12)
        if idx > 0: p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 4: System Architecture
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, prs)
    add_header(s4, "System Architecture & Simulation Pipeline", "3. Architecture")

    if os.path.exists(ARCH_FIG):
        s4.shapes.add_picture(ARCH_FIG, Inches(0.8), Inches(1.5), Inches(7.2), Inches(5.3))
    else:
        add_card(s4, Inches(0.8), Inches(1.5), Inches(7.2), Inches(5.3), "System Pipeline Architecture")

    # Right side explanatory cards
    add_card(s4, Inches(8.3), Inches(1.5), Inches(4.2), Inches(5.3), "Key Architectural Innovations")
    tb = s4.shapes.add_textbox(Inches(8.5), Inches(2.0), Inches(3.8), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True

    arch_points = [
        ("Admission Control: ", "Jobs exceeding budget caps or with impossible deadlines are rejected upfront, not silently dropped."),
        ("Decoupled Data Staging: ", "Data transfers across the WAN occupy the network link without prematurely holding CPU cores in the target cluster."),
        ("Power & PUE Modeling: ", "Linear power scaling (P_idle to P_max) attributed proportionally across co-located jobs, scaled by regional PUE (1.15 to 1.60)."),
        ("Calibrated Forecast Noise: ", "Autoregressive AR(1) error process (ρ=0.7, ε=0.15) matching real National Grid ESO forecast accuracy."),
        ("Ground-Truth Carbon Billing: ", "Scheduler decides via forecasts; simulation charges actual emissions using time-weighted window integration.")
    ]
    for idx, (b_t, b_d) in enumerate(arch_points):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = b_t; r1.font.bold = True; r1.font.color.rgb = BLUE; r1.font.size = Pt(11.5)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11.5)
        if idx > 0: p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 5: Mathematical Formulation (GreenOps MOO)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, prs)
    add_header(s5, "GreenOps MOO: Algorithm & Mathematical Formulation", "4. Optimization Heuristic")

    # Hard constraints box
    add_card(s5, Inches(0.8), Inches(1.5), Inches(11.7), Inches(1.3), "1. Feasible Candidate Search Space (Hard Constraints)")
    tb = s5.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Candidates x = (r, s) where region r ∈ Allowed_Regions, total cost ≤ Budget, and start s ≤ Deadline - Runtime - Transfer_Time.\n• Strict jobs enforce s = now (zero deferral). Flexible jobs explore candidate hours up to max_wait (W = 12h)."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # 3 Objectives
    c1 = add_card(s5, Inches(0.8), Inches(3.0), Inches(3.7), Inches(2.6), "Objective 1: Carbon C(x)")
    tb = s5.shapes.add_textbox(Inches(1.0), Inches(3.5), Inches(3.3), Inches(2.0))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "C(x) = (E·I_forecast + C_net) × (1 + κ·σ(s - now))"
    p.font.size = Pt(11.5); p.font.bold = True; p.font.color.rgb = EMERALD
    p2 = tf.add_paragraph()
    p2.text = "• Confidence Gate: Inflates future carbon by horizon uncertainty σ(h).\n• Scheduler only waits if the forecast dip exceeds potential forecast error."
    p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    c2 = add_card(s5, Inches(4.8), Inches(3.0), Inches(3.7), Inches(2.6), "Objective 2: Cost K(x)")
    tb = s5.shapes.add_textbox(Inches(5.0), Inches(3.5), Inches(3.3), Inches(2.0))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "K(x) = c_j·d_j·price_r + π_egress·g_j·[r ≠ home]"
    p.font.size = Pt(11.5); p.font.bold = True; p.font.color.rgb = BLUE
    p2 = tf.add_paragraph()
    p2.text = "• Compute compute fees plus WAN egress charges ($0.02/GB).\n• Protects against remote dispatch when input datasets are large (data gravity)."
    p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    c3 = add_card(s5, Inches(8.8), Inches(3.0), Inches(3.7), Inches(2.6), "Objective 3: SLA Risk R(x)")
    tb = s5.shapes.add_textbox(Inches(9.0), Inches(3.5), Inches(3.3), Inches(2.0))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "R(x) = ((s - now) / (latest_start - now))²"
    p.font.size = Pt(11.5); p.font.bold = True; p.font.color.rgb = AMBER
    p2 = tf.add_paragraph()
    p2.text = "• Convex Slack Consumption: Waiting is cheap when plenty of slack exists, but exponentially penalized near deadline.\n• Completely eliminates deferral-induced SLA violations."
    p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    # Selection modes bottom bar
    add_card(s5, Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.2), "Decision Modes & Hourly Re-Planning")
    tb = s5.shapes.add_textbox(Inches(1.0), Inches(6.2), Inches(11.3), Inches(0.7))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Weighted Sum: score = 0.6·p_j·(C/Cmax) + 0.2·(K/Kmax) + 0.2·R  |  Pareto Mode: Non-dominated filter + weighted Tchebycheff knee\n• Dynamic Re-planning: Deferred jobs sleep in SimPy and re-evaluate their decision every 1 hour with a fresher forecast."
    p.font.size = Pt(11.5); p.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 6: Experimental Setup & Datasets
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, prs)
    add_header(s6, "Experimental Setup & Real-World Traces", "5. Evaluation Methodology")

    add_card(s6, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4), "1. Historical Grid Carbon Traces (2024)")
    tb = s6.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.3), Inches(4.7))
    tf = tb.text_frame; tf.word_wrap = True
    r_traces = [
        ("Germany (DE): ", "Mean 353 (win) / 331 (sum) g/kWh. High renewable volatility. Derived from Energy-Charts API 15-min mix × IPCC lifecycle factors."),
        ("Norway (NO): ", "Mean 28 (win) / 31 (sum) g/kWh. Pure hydro baseline. Energy-Charts API."),
        ("France (FR): ", "Mean 52 (win) / 29 (sum) g/kWh. Clean nuclear/hydro baseload. Energy-Charts API."),
        ("Poland (PL): ", "Mean 586 (win) / 626 (sum) g/kWh. Coal-heavy grid. Energy-Charts API."),
        ("Great Britain (GB): ", "Mean 159 (win) / 113 (sum) g/kWh. Real actual + forecast intensity from National Grid ESO API."),
        ("India (IN): ", "Mean 708 (win) / 633 (sum) g/kWh. Calibrated model based on CEA CO2 Baseline Database.")
    ]
    for idx, (b_t, b_d) in enumerate(r_traces):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_t; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(11)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11)
        if idx > 0: p.space_before = Pt(4)

    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), "2. Evaluated Workload Benchmarks")
    tb = s6.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(5.3), Inches(4.7))
    tf = tb.text_frame; tf.word_wrap = True
    w_points = [
        ("Synthetic Multi-Season Suite (E1–E7):", ""),
        ("• 300 heterogeneous jobs per run", "spanning strict (30%), batch (40%), and flexible (30%) classes."),
        ("• 20 random seeds × 2 seasons", "(Jan & Jul 2024) = 40 paired runs per scheduler."),
        ("• Independent Tuning Seeds", "Weights tuned on seeds 100–104; evaluated on seeds 0–19."),
        ("Alibaba Cluster Trace v2018 (P1–P5):", ""),
        ("• Industrial Scale: ", "~45,000 real batch jobs per run across 3,840 vCPUs (80 nodes × 16 cores per region) over 8 full days."),
        ("• Real Job Attributes: ", "Replays empirical arrival bursts, runtimes, and CPU demands."),
        ("• Data Gravity Instrument: ", "Staging overhead (450 GB/h, $0.02/GB, 0.005 kWh/GB)."),
        ("• Literature Baselines: ", "Compared against Wait Awhile [Wiesner '21] and Online Threshold [Lechowicz '24].")
    ]
    for idx, (b_t, b_d) in enumerate(w_points):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        if not b_d:
            p.text = b_t; p.font.bold = True; p.font.size = Pt(12); p.font.color.rgb = BLUE
            p.space_before = Pt(8)
        else:
            r1 = p.add_run(); r1.text = b_t + " "; r1.font.bold = True; r1.font.color.rgb = TEXT_WHITE; r1.font.size = Pt(11)
            r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11)
            p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 7: Headline Results — Main Comparison (E1)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, prs)
    add_header(s7, "Main Comparative Results (Experiment E1)", "6. Results")

    fig2_path = os.path.join(FIGS_DIR, "fig2_main_comparison.png")
    if os.path.exists(fig2_path):
        s7.shapes.add_picture(fig2_path, Inches(0.8), Inches(1.5), Inches(6.2), Inches(5.3))
    else:
        add_card(s7, Inches(0.8), Inches(1.5), Inches(6.2), Inches(5.3), "E1 Comparison Figure")

    # Table on right side
    add_card(s7, Inches(7.2), Inches(1.5), Inches(5.3), Inches(5.3), "Headline Metrics Summary (40 Runs)")
    tb = s7.shapes.add_textbox(Inches(7.4), Inches(2.0), Inches(4.9), Inches(4.6))
    tf = tb.text_frame; tf.word_wrap = True

    e1_findings = [
        ("−26.8% Carbon vs Round Robin: ", "Massive operational emission reduction compared to carbon-agnostic scheduling."),
        ("−5.3% Carbon vs Greenest Region: ", "Statistically significant (p < 0.001, paired permutation test) for only +0.65% cost."),
        ("Within 1.2% of Temporal Green: ", "Nearly matches aggressive greedy deferral carbon with 90% FEWER SLA violations (0.28 vs 2.80 per run)."),
        ("52% Lower Tail Latency: ", "GreenOps p95 latency is 7.3h vs 15.0h for Temporal Green. Strict jobs experience 0 wait."),
        ("Cost-Only is Environmentally Catastrophic: ", "Cost-Only emits 119.6 kg (+58% over GreenOps) by pinning work to coal-heavy India.")
    ]
    for idx, (b_t, b_d) in enumerate(e1_findings):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_t; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(11.5)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11.5)
        if idx > 0: p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 8: Pareto Frontier & Forecast Uncertainty (E2 & E3)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, prs)
    add_header(s8, "Pareto Frontier & Robustness to Forecast Error", "7. Deep-Dive Analysis")

    # E2 Left
    add_card(s8, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3), "Pareto Frontier Sweep (E2)")
    fig3_path = os.path.join(FIGS_DIR, "fig3_pareto_frontier.png")
    if os.path.exists(fig3_path):
        s8.shapes.add_picture(fig3_path, Inches(1.0), Inches(2.0), Inches(5.3), Inches(3.2))
    tb = s8.shapes.add_textbox(Inches(1.0), Inches(5.3), Inches(5.3), Inches(1.3))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Hypervolume: GreenOps Pareto scores 0.754 and Weighted scores 0.737 vs 0.524 for all 4 baselines combined.\n• Spans continuous trade-off from cost-optimal ($367, 130 kg) to carbon-optimal ($455, 68 kg)."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_MUTED

    # E3 Right
    add_card(s8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3), "Forecast Noise Sensitivity (E3)")
    fig4_path = os.path.join(FIGS_DIR, "fig4_forecast_sensitivity.png")
    if os.path.exists(fig4_path):
        s8.shapes.add_picture(fig4_path, Inches(7.0), Inches(2.0), Inches(5.3), Inches(3.2))
    tb = s8.shapes.add_textbox(Inches(7.0), Inches(5.3), Inches(5.3), Inches(1.3))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• Error swept from 0% (oracle) to 50%.\n• Temporal Green carbon rises +4.9%; GreenOps rises only +1.9%.\n• At ≥ 30% error, GreenOps emits LESS carbon than Temporal Green due to hourly re-planning."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 9: Practical Limits of Shifting (E4 & E5)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, prs)
    add_header(s9, "Practical Limits of Shifting & Load Scaling", "8. Acun et al. Verification")

    add_card(s9, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3), "Temporal Flexibility Window Saturation (E4)")
    fig5_path = os.path.join(FIGS_DIR, "fig5_max_wait.png")
    if os.path.exists(fig5_path):
        s9.shapes.add_picture(fig5_path, Inches(1.0), Inches(2.0), Inches(5.3), Inches(3.2))
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(5.3), Inches(5.3), Inches(1.3))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• 95% of total temporal reduction captured within first 2–4 hours.\n• Deferral windows beyond 6h add severe latency with negligible emissions gain (verifying Acun et al. EuroSys '24 critique)."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_MUTED

    add_card(s9, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3), "System Load & Saturation Sensitivity (E5)")
    fig6_path = os.path.join(FIGS_DIR, "fig6_load.png")
    if os.path.exists(fig6_path):
        s9.shapes.add_picture(fig6_path, Inches(7.0), Inches(2.0), Inches(5.3), Inches(3.2))
    tb = s9.shapes.add_textbox(Inches(7.0), Inches(5.3), Inches(5.3), Inches(1.3))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "• At low load (0.5×), greedy spatial shifting is near-optimal.\n• At 2× load, clean Norway saturates. GreenOps advantage widens to −9.8% carbon vs Greenest Region while TG suffers 15.5 violations/run."
    p.font.size = Pt(11); p.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 10: Industrial Scale Alibaba Trace Evaluation
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, prs)
    add_header(s10, "Industrial Scale: Alibaba Cluster Trace Replay", "9. Trace-Driven Study")

    add_card(s10, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.3), "Replay of 45,000 Real Jobs across 3,840 vCPUs (8 Days)")
    tb = s10.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.5))
    tf = tb.text_frame; tf.word_wrap = True

    p_findings = [
        ("Selective Deferral Relieves Cluster Congestion: ", "Under bursty diurnal traffic, zero-deferral policies (Round Robin, Cost Only, Greenest Region) miss > 4.1% of strict deadlines due to queueing contention. GreenOps defers flexible batch work, freeing cores and slashing strict SLA violations to 0.06% (a 70× improvement)."),
        ("The 'No Free Lunch' Carbon-SLA Frontier: ", "The forecast-free Online Threshold policy [Lechowicz '24] achieves the lowest raw carbon (5.11 t), but causes 3.44% SLA violations (10× GreenOps). GreenOps represents the superior production operating point: 5.39 t carbon with only 0.33% total violations."),
        ("Data Gravity is Primarily an Economic Barrier: ", "Network energy (0.005 kWh/GB) represents < 2% of emissions, but WAN egress fees ($0.02/GB) explode costs. Transfer-unaware GreenOps moved 40% of jobs and spent +11% more in egress fees. Transfer-aware GreenOps intelligently bounded movement to 21%."),
        ("Temporal-Only Shifting is Insufficient: ", "Wait Awhile [Wiesner '21], which pins jobs to their home region, emitted +9.4% MORE carbon than greedy spatial shifting. Spatial shifting remains the essential baseline foundation.")
    ]
    for idx, (b_t, b_d) in enumerate(p_findings):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_t; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(12)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(12)
        if idx > 0: p.space_before = Pt(10)

    # =========================================================================
    # SLIDE 11: Interactive Cloud Dashboard
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, prs)
    add_header(s11, "Interactive Cloud Dashboard & Demonstration", "10. Live Software Artifact")

    add_card(s11, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3), "Real-Time Workload Orchestration UI")
    tb = s11.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.3), Inches(4.5))
    tf = tb.text_frame; tf.word_wrap = True

    dash_features = [
        ("Interactive Workload Assignment: ", "Submit custom jobs or 1-click presets (Interactive API, Batch ETL, ML Training, EU Sovereign)."),
        ("Live Regional Telemetry: ", "6 grid zones with real-time carbon intensity badges, electricity prices, PUE, and 24h trace sparklines."),
        ("Simulated Execution & Gantt Timeline: ", "Visualizes lifecycle phases: WAN Data Staging → Deferral Wait → Compute Execution vs Deadline."),
        ("Side-by-Side Multi-Scheduler Benchmark: ", "Compares the assigned job across all 7 schedulers in parallel, detailing carbon and cost deltas."),
        ("Candidate Decision Inspector: ", "Inspects raw ranked (region, start time) options scored by GreenOps MOO.")
    ]
    for idx, (b_t, b_d) in enumerate(dash_features):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "✓ " + b_t; r1.font.bold = True; r1.font.color.rgb = BLUE; r1.font.size = Pt(11.5)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11.5)
        if idx > 0: p.space_before = Pt(6)

    add_card(s11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3), "Software Implementation Architecture")
    tb = s11.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(5.3), Inches(4.5))
    tf = tb.text_frame; tf.word_wrap = True

    tech_specs = [
        ("Threaded Python Backend: ", "Uses standard library http.server.ThreadingHTTPServer with Connection: close headers for concurrent browser requests."),
        ("Zero External Dependencies: ", "Runs out of the box with Python standard library and SimPy. No heavy web framework overhead."),
        ("In-Memory Trace Caching: ", "Sub-millisecond response time for single-job simulations and multi-scheduler comparison runs."),
        ("Resilient Error Handling: ", "Infeasible jobs render clear 'Rejected at Admission' cards rather than crashing."),
        ("1-Click Windows Launcher: ", "Includes interactive_dashboard/run_dashboard.bat for viva defense demonstration.")
    ]
    for idx, (b_t, b_d) in enumerate(tech_specs):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_t; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(11.5)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11.5)
        if idx > 0: p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 12: Verification & Engineering Rigor
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12, prs)
    add_header(s12, "Verification, Testing & Statistical Rigor", "11. Quality Assurance")

    # 4 Big Stat Cards
    c1 = add_card(s12, Inches(0.8), Inches(1.6), Inches(2.7), Inches(2.2))
    tb = s12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(2.3), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "51 Tests"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = EMERALD
    p2 = tf.add_paragraph(); p2.text = "Automated unit & integration tests across test_greenops.py and test_trace_network.py (100% passing)."; p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    c2 = add_card(s12, Inches(3.8), Inches(1.6), Inches(2.7), Inches(2.2))
    tb = s12.shapes.add_textbox(Inches(4.0), Inches(1.8), Inches(2.3), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "0.32 s"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = BLUE
    p2 = tf.add_paragraph(); p2.text = "Total test suite execution wall-clock time. Discrete event simulation is highly efficient."; p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    c3 = add_card(s12, Inches(6.8), Inches(1.6), Inches(2.7), Inches(2.2))
    tb = s12.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(2.3), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "p < 0.001"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = AMBER
    p2 = tf.add_paragraph(); p2.text = "Two-sided paired sign-flip permutation tests (20,000 permutations) confirm statistical significance."; p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    c4 = add_card(s12, Inches(9.8), Inches(1.6), Inches(2.7), Inches(2.2))
    tb = s12.shapes.add_textbox(Inches(10.0), Inches(1.8), Inches(2.3), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "0.1 ms"; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = ROSE
    p2 = tf.add_paragraph(); p2.text = "Decision latency per job. Linear scalability allows 5,000 jobs to simulate in under 0.5s."; p2.font.size = Pt(11); p2.font.color.rgb = TEXT_MUTED; p2.space_before = Pt(4)

    # Narrative Card Below
    add_card(s12, Inches(0.8), Inches(4.2), Inches(11.7), Inches(2.6), "Methodological Safeguards")
    tb = s12.shapes.add_textbox(Inches(1.1), Inches(4.7), Inches(11.1), Inches(1.9))
    tf = tb.text_frame; tf.word_wrap = True
    safeguards = [
        ("Strict Tuning Separation: ", "Default MOO weights (0.6 / 0.2 / 0.2), κ (0.5), and quadratic risk exponent were tuned exclusively on held-out seeds 100–104 and never on evaluation seeds 0–19."),
        ("Zero Dropped Jobs: ", "Queueing logic ensures jobs facing temporary regional saturation wait on resource release events rather than being discarded."),
        ("No Oracle Leakage: ", "Scheduler decisions strictly receive forecast signals contaminated with horizon noise and AR(1) autocorrelation. True ground-truth carbon is revealed only at completion."),
        ("Decoupled Network Staging: ", "Verified via test_transfer_does_not_hold_cpus: data transfers use the network link without holding compute CPUs in the target region.")
    ]
    for idx, (b_t, b_d) in enumerate(safeguards):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "✓ " + b_t; r1.font.bold = True; r1.font.color.rgb = TEXT_WHITE; r1.font.size = Pt(12)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(12)
        if idx > 0: p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 13: Conclusion & Future Work
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13, prs)
    add_header(s13, "Conclusion & Future Work", "12. Project Wrap-Up")

    add_card(s13, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.3), "Project Conclusions")
    tb = s13.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.3), Inches(4.5))
    tf = tb.text_frame; tf.word_wrap = True
    conclusions = [
        ("Carbon-Aware Scheduling Works: ", "Reduces carbon emissions by 26.8% vs Round Robin and 5.3% vs greedy spatial greening at negligible cost (+0.65%)."),
        ("Multi-Objective Balance Beats Greed: ", "Achieves near-best carbon with 90% fewer SLA violations than aggressive deferral by enforcing quadratic SLA risk penalties."),
        ("Robust Under Noise: ", "Hourly re-planning and confidence gating prevent bad decisions under forecast errors up to 50%."),
        ("Selective Deferral Relieves Peak Load: ", "On real cluster traces, deferring flexible workloads reduces strict deadline misses from 4.27% to 0.06%."),
        ("Understanding the Limits: ", "Moving workloads provides the primary dividend; deferrals beyond 2–4 hours offer rapidly diminishing returns.")
    ]
    for idx, (b_t, b_d) in enumerate(conclusions):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "• " + b_t; r1.font.bold = True; r1.font.color.rgb = EMERALD; r1.font.size = Pt(11.5)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(11.5)
        if idx > 0: p.space_before = Pt(6)

    add_card(s13, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3), "Future Research Directions")
    tb = s13.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(5.3), Inches(4.5))
    tf = tb.text_frame; tf.word_wrap = True
    future = [
        ("Kubernetes Multi-Cluster Extender: ", "Deploy GreenOps as an out-of-tree Kubernetes scheduler extender integrating with KEDA and the Carbon Aware SDK."),
        ("Marginal vs Average Emissions: ", "Incorporate WattTime MOER (marginal operating emissions rate) to quantify the consequential grid impacts of load shifting."),
        ("Capacity Reservations: ", "Reserve future cluster time slots for deferred jobs to eliminate rare saturation-driven queueing delays."),
        ("Tenant-Level Online Learning: ", "Implement contextual bandits or RL to learn tenant-specific weight profiles dynamically based on observed slack and budget elasticity.")
    ]
    for idx, (b_t, b_d) in enumerate(future):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run(); r1.text = "→ " + b_t; r1.font.bold = True; r1.font.color.rgb = BLUE; r1.font.size = Pt(12)
        r2 = p.add_run(); r2.text = b_d; r2.font.color.rgb = TEXT_MUTED; r2.font.size = Pt(12)
        if idx > 0: p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 14: Q&A / Thank You
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14, prs)

    banner = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(0.15), Inches(3.8))
    banner.fill.solid()
    banner.fill.fore_color.rgb = EMERALD
    banner.line.fill.background()

    tb = s14.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.2), Inches(3.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "THANK YOU"
    p.font.size = Pt(40); p.font.bold = True; p.font.color.rgb = TEXT_WHITE
    p2 = tf.add_paragraph()
    p2.text = "Questions & Answers"
    p2.font.size = Pt(22); p2.font.bold = True; p2.font.color.rgb = EMERALD; p2.space_before = Pt(6)

    p3 = tf.add_paragraph()
    p3.text = "GreenOps Cloud Orchestration — Spatial and Temporal Demand Shifting for Carbon-Aware Cloud Workload Scheduling"
    p3.font.size = Pt(14); p3.font.color.rgb = TEXT_MUTED; p3.space_before = Pt(12)

    p4 = tf.add_paragraph()
    p4.text = "Project Team: SANJEEVKUMAR K S (24MID0172) · NITHISH KUMAR (24MIC0032) · MUHAMMED FAHEEM K (24MID0158)\nVellore Institute of Technology, Vellore"
    p4.font.size = Pt(13); p4.font.color.rgb = TEXT_WHITE; p4.space_before = Pt(12)

    # Output paths
    final_ppt = os.path.join(DOCS_DIR, "GreenOps_Final_Presentation.pptx")
    std_ppt = os.path.join(DOCS_DIR, "GreenOps_Presentation.pptx")

    prs.save(final_ppt)
    prs.save(std_ppt)
    print(f"Successfully generated: {final_ppt}")
    print(f"Synchronized with: {std_ppt}")


if __name__ == "__main__":
    build_presentation()
