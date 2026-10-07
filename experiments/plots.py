"""
Figures for the GreenOps evaluation.

Reads results/evaluation/*.csv (produced by experiments/evaluation.py)
and writes PNG figures to results/figures/.

    python -m experiments.plots
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import CORE_REGIONS, load_traces


EVAL_DIR = os.path.join(PROJECT_ROOT, "results", "evaluation")
FIG_DIR = os.path.join(PROJECT_ROOT, "results", "figures")


# ============================================================
# STYLE
#
# Categorical slots in fixed order (validated reference palette).
# Colour follows the entity: every scheduler keeps its colour in
# every figure.
# ============================================================

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"

NEUTRAL = "#b9b8b3"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"

SCHEDULER_COLORS = {
    "GreenOps MOO": BLUE,
    "Temporal Green": ORANGE,
    "Greenest Region": AQUA,
    "Round Robin": YELLOW,
    "Cost Only": MAGENTA,
    "GreenOps (spatial only)": NEUTRAL,
    "GreenOps Pareto": NEUTRAL,
}

REGION_COLORS = {
    "Norway": BLUE,
    "Germany": ORANGE,
    "India": AQUA,
}

ORDER = [
    "Cost Only",
    "Round Robin",
    "Greenest Region",
    "GreenOps (spatial only)",
    "GreenOps Pareto",
    "Temporal Green",
    "GreenOps MOO",
]

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "lines.linewidth": 2,
    "font.family": "DejaVu Sans",
})


def save(fig, name):

    os.makedirs(FIG_DIR, exist_ok=True)

    path = os.path.join(FIG_DIR, name)

    fig.savefig(path, dpi=180, bbox_inches="tight")

    plt.close(fig)

    print(f"  wrote {os.path.relpath(path, PROJECT_ROOT)}")


def read(name):
    return pd.read_csv(os.path.join(EVAL_DIR, name))


def end_label(ax, x, y, text, color=INK_2, dy=0):
    ax.annotate(
        text, (x, y), xytext=(6, dy), textcoords="offset points",
        va="center", fontsize=8.5, color=color,
    )


# ============================================================
# FIG 1 - CARBON TRACES
# ============================================================

def fig_traces():

    fig, axes = plt.subplots(2, 1, figsize=(9, 5.2), sharey=True)

    for ax, period, title in zip(
        axes,
        ("winter_2024", "summer_2024"),
        ("Winter (8-14 Jan 2024)", "Summer (1-7 Jul 2024)"),
    ):

        traces = load_traces(period, CORE_REGIONS)

        hours = np.arange(24 * 7)

        for name in CORE_REGIONS:

            values = np.array(traces[name][: len(hours)])

            ax.plot(hours / 24, values, color=REGION_COLORS[name],
                    linewidth=1.6)

            end_label(ax, hours[-1] / 24, values[-1], name,
                      color=INK_2)

        ax.set_title(title, loc="left")
        ax.set_xlim(0, 7)
        ax.set_ylim(0, 900)
        ax.set_ylabel("gCO₂eq / kWh")

    axes[-1].set_xlabel("Day of trace (UTC)")

    fig.suptitle(
        "Hourly grid carbon intensity of the three core regions",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.text(
        0.01, -0.02,
        "Germany and Norway: Energy-Charts generation mix x IPCC AR5 "
        "lifecycle factors. India: modelled (CEA calibrated).",
        fontsize=7.5, color=INK_2,
    )

    fig.tight_layout()

    save(fig, "fig1_carbon_traces.png")


# ============================================================
# FIG 2 - MAIN COMPARISON (small multiples)
# ============================================================

def fig_main():

    table = read("e1_main_summary.csv")

    pooled = table[table["period"] == "both"].set_index("label").loc[ORDER]

    panels = [
        ("total_carbon_g", "Carbon emitted (kgCO₂eq)", 1 / 1000),
        ("total_cost", "Compute cost ($)", 1),
        ("p95_latency", "p95 job latency (h)", 1),
        ("sla_violations", "SLA violations per run", 1),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True)

    y = np.arange(len(ORDER))

    for ax, (metric, title, scale) in zip(axes, panels):

        means = pooled[f"{metric}_mean"] * scale
        stds = pooled[f"{metric}_std"] * scale

        colors = [
            BLUE if label == "GreenOps MOO" else NEUTRAL
            for label in ORDER
        ]

        lower = np.minimum(stds, means)

        ax.barh(y, means, xerr=[lower, stds], color=colors, height=0.62,
                error_kw=dict(ecolor=INK_2, elinewidth=1, capsize=2))

        for yi, value, err in zip(y, means, stds):
            ax.annotate(
                f"{value:,.1f}" if value < 100 else f"{value:,.0f}",
                (value + err, yi), xytext=(4, 0),
                textcoords="offset points",
                va="center", fontsize=7.5, color=INK,
            )

        ax.set_xlim(0, (means + stds).max() * 1.25)

        ax.set_title(title, loc="left", fontsize=9.5)
        ax.grid(axis="y", visible=False)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(ORDER)

    fig.suptitle(
        "Scheduler comparison - 300 jobs, 3 regions, 20 seeds x 2 seasons "
        "(mean ± std), realistic forecasts",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.tight_layout()

    save(fig, "fig2_main_comparison.png")


# ============================================================
# FIG 3 - PARETO FRONTIER
# ============================================================

def fig_pareto():

    points = read("e2_sweep_points.csv")
    hv = read("e2_hypervolume.csv").set_index("scheduler")

    fig, ax = plt.subplots(figsize=(8, 5.4))

    for scheduler, color, label in (
        ("greenops_moo", BLUE, "GreenOps MOO - weighted sum"),
        ("greenops_pareto", ORANGE, "GreenOps - Pareto + Tchebycheff"),
    ):

        group = points[points["scheduler"] == scheduler]

        ax.scatter(
            group["total_cost"], group["total_carbon_g"] / 1000,
            s=26, color=color, alpha=0.75, edgecolor=SURFACE,
            linewidth=0.8,
            label=f"{label}  (HV = {hv.loc[scheduler, 'hypervolume']:.3f})",
        )

    baselines = points[~points["scheduler"].str.startswith("greenops")]

    ax.scatter(
        baselines["total_cost"], baselines["total_carbon_g"] / 1000,
        s=70, marker="D", color=INK, edgecolor=SURFACE, linewidth=1.5,
        zorder=4,
        label=f"Baselines  (HV together = "
              f"{hv.loc['all_baselines', 'hypervolume']:.3f})",
    )

    offsets = {
        "Cost Only": (8, -10),
        "Round Robin": (8, -10),
        "Greenest Region": (-30, 40),
        "Temporal Green": (-40, -22),
    }

    for _, row in baselines.iterrows():
        ax.annotate(
            row["label"],
            (row["total_cost"], row["total_carbon_g"] / 1000),
            xytext=offsets.get(row["label"], (8, -10)),
            textcoords="offset points", fontsize=8.5, color=INK,
            arrowprops=(
                dict(arrowstyle="-", color=INK_2, linewidth=0.8)
                if row["label"] == "Greenest Region" else None
            ),
        )

    default = points[
        (points["scheduler"] == "greenops_moo")
        & np.isclose(points["param_carbon_weight"], 0.6)
        & np.isclose(points["param_cost_weight"], 0.2)
    ]

    ax.scatter(
        default["total_cost"], default["total_carbon_g"] / 1000,
        s=160, facecolor="none", edgecolor=BLUE, linewidth=2, zorder=5,
    )

    for _, row in default.iterrows():
        ax.annotate(
            "GreenOps default\n(0.6 / 0.2 / 0.2)",
            (row["total_cost"], row["total_carbon_g"] / 1000),
            xytext=(-150, -40), textcoords="offset points",
            fontsize=8.5, color=INK,
            arrowprops=dict(arrowstyle="-", color=INK_2, linewidth=0.8),
        )

    ax.set_xlabel("Compute cost per run ($) → lower is better")
    ax.set_ylabel("Carbon per run (kgCO₂eq) → lower is better")

    ax.set_title(
        "Carbon-cost trade-off: weight sweep over the objective simplex",
        loc="left",
    )

    ax.legend(loc="upper right")

    fig.tight_layout()

    save(fig, "fig3_pareto_frontier.png")


# ============================================================
# FIG 4 - FORECAST ERROR SENSITIVITY
# ============================================================

def fig_forecast():

    table = read("e3_forecast_summary.csv")

    variants = [
        ("temporal_green", "Temporal Green", ORANGE, "-"),
        ("greenops_moo", "GreenOps MOO (gate)", BLUE, "-"),
        ("greenops_moo_nogate", "GreenOps MOO (no gate)", BLUE, "--"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True)

    for col, (scenario, title) in enumerate((
        ("core", "3 regions (spatial + temporal)"),
        ("germany_only", "Germany only (temporal shifting only)"),
    )):

        data = table[table["scenario"] == scenario]

        greenest = data[data["variant"] == "greenest_region"]

        for row, (metric, ylabel, scale) in enumerate((
            ("total_carbon_g", "Carbon (kgCO₂eq)", 1 / 1000),
            ("sla_violations", "SLA violations / run", 1),
        )):

            ax = axes[row, col]

            ref = greenest[f"{metric}_mean"].iloc[0] * scale

            ax.axhline(ref, color=NEUTRAL, linewidth=1.5, linestyle=":")

            end_label(ax, 0.5, ref, "Greenest Region (no forecast)", dy=7)

            for variant, label, color, style in variants:

                series = data[data["variant"] == variant].sort_values(
                    "forecast_error"
                )

                x = series["forecast_error"] * 100
                yv = series[f"{metric}_mean"] * scale

                ax.plot(x, yv, color=color, linestyle=style,
                        marker="o", markersize=4, label=label)

            if row == 0:
                ax.set_title(title, loc="left")

            ax.set_ylabel(ylabel)

            if row == 1:
                ax.set_xlabel("Forecast error at 24 h horizon (%)")

    axes[0, 0].axvline(15, color=GRID, linewidth=6, zorder=0)
    axes[0, 0].annotate("calibrated\n(GB ESO)", (15, axes[0, 0].get_ylim()[1]),
                        xytext=(3, -14), textcoords="offset points",
                        fontsize=7.5, color=INK_2)

    handles, labels = axes[0, 1].get_legend_handles_labels()

    fig.legend(handles, labels, loc="upper right", ncol=3,
               bbox_to_anchor=(1.0, 1.0))

    fig.suptitle(
        "Robustness to carbon-forecast error (10 seeds x 2 seasons)",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.tight_layout()

    save(fig, "fig4_forecast_sensitivity.png")


# ============================================================
# FIG 5 - MAX WAIT (limits of temporal shifting)
# ============================================================

def fig_maxwait():

    table = read("e4_maxwait_summary.csv")

    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True)

    for col, (scenario, title) in enumerate((
        ("core", "3 regions"),
        ("germany_only", "Germany only"),
    )):

        data = table[table["scenario"] == scenario]

        for row, (metric, ylabel, scale) in enumerate((
            ("total_carbon_g", "Carbon (kgCO₂eq)", 1 / 1000),
            ("p95_latency", "p95 latency (h)", 1),
        )):

            ax = axes[row, col]

            for label, color in (("Temporal Green", ORANGE),
                                 ("GreenOps MOO", BLUE)):

                series = data[data["label"] == label].sort_values("max_wait")

                ax.plot(series["max_wait"],
                        series[f"{metric}_mean"] * scale,
                        color=color, marker="o", markersize=4, label=label)

            if row == 0:
                ax.set_title(title, loc="left")

            ax.set_ylabel(ylabel)

            if row == 1:
                ax.set_xlabel("Maximum deferral window (h)")

    axes[0, 0].legend()

    fig.suptitle(
        "How much temporal flexibility is useful? (10 seeds x 2 seasons)",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.tight_layout()

    save(fig, "fig5_max_wait.png")


# ============================================================
# FIG 6 - LOAD SENSITIVITY
# ============================================================

def fig_load():

    table = read("e5_load_summary.csv")

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))

    greenest = table[table["label"] == "Greenest Region"].set_index(
        "load_scale"
    )["total_carbon_g_mean"]

    for label in ("Round Robin", "Greenest Region", "Temporal Green",
                  "GreenOps MOO"):

        series = table[table["label"] == label].sort_values("load_scale")

        color = SCHEDULER_COLORS[label]

        reduction = (
            series["total_carbon_g_mean"].values
            / greenest.loc[series["load_scale"]].values - 1
        ) * 100

        axes[0].plot(series["load_scale"], reduction, color=color,
                     marker="o", markersize=4, label=label)

        axes[1].plot(series["load_scale"], series["sla_violations_mean"],
                     color=color, marker="o", markersize=4, label=label)

    axes[0].set_title("Carbon vs Greenest Region (%)", loc="left")
    axes[0].set_ylabel("Δ carbon (%)")
    axes[1].set_title("SLA violations per run (300 jobs)", loc="left")

    for ax in axes:
        ax.set_xlabel("Load (x baseline arrival rate)")

    axes[1].legend()

    fig.suptitle(
        "Effect of system load (10 seeds x 2 seasons)",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.tight_layout()

    save(fig, "fig6_load.png")


# ============================================================
# FIG 7 - LATENCY CDF
# ============================================================

def fig_latency_cdf():

    jobs = read("e1_main_jobs.csv")

    jobs = jobs[jobs["status"] == "completed"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)

    for ax, classes, title in (
        (axes[0], ("strict",), "Strict (real-time) jobs"),
        (axes[1], ("batch", "flexible"), "Batch + flexible jobs"),
    ):

        subset = jobs[jobs["flexibility"].isin(classes)]

        for label in ("Round Robin", "Greenest Region", "Temporal Green",
                      "GreenOps MOO"):

            values = np.sort(subset[subset["label"] == label]["latency"])

            cdf = np.arange(1, len(values) + 1) / len(values)

            ax.step(values, cdf, where="post",
                    color=SCHEDULER_COLORS[label], label=label)

        ax.set_title(title, loc="left")
        ax.set_xlabel("Job latency: completion - arrival (h)")

    axes[0].set_ylabel("Fraction of jobs")
    axes[1].legend(loc="lower right")

    fig.suptitle(
        "Latency distribution (E1, seeds 0-4, both seasons)",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )

    fig.tight_layout()

    save(fig, "fig7_latency_cdf.png")


# ============================================================
# FIG 8 - WHERE DID THE WORK RUN?
# ============================================================

def fig_region_share():

    runs = read("e1_main_runs.csv")

    shares = runs.groupby("label")[
        [f"share_{r}" for r in ("Norway", "Germany", "India")]
    ].mean().loc[ORDER]

    fig, ax = plt.subplots(figsize=(9, 3.8))

    left = np.zeros(len(shares))

    y = np.arange(len(shares))

    for region in ("Norway", "Germany", "India"):

        values = shares[f"share_{region}"].values

        ax.barh(y, values, left=left, color=REGION_COLORS[region],
                height=0.62, edgecolor=SURFACE, linewidth=2, label=region)

        for yi, (l, v) in enumerate(zip(left, values)):
            if v > 8:
                ax.text(l + v / 2, yi, f"{v:.0f}%", ha="center",
                        va="center", fontsize=7.5, color="white")

        left += values

    ax.set_yticks(y)
    ax.set_yticklabels(ORDER)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of CPU-hours (%)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13))

    ax.set_title("Spatial placement by scheduler", loc="left", pad=26)

    fig.tight_layout()

    save(fig, "fig8_region_share.png")


# ============================================================
# MAIN
# ============================================================

def main():

    print("Generating figures ...")

    fig_traces()
    fig_main()
    fig_pareto()
    fig_forecast()
    fig_maxwait()
    fig_load()
    fig_latency_cdf()
    fig_region_share()


if __name__ == "__main__":
    main()
