"""
Column-width figures for the workshop paper (reads results/paper/*.csv).

    python -m experiments.plots_paper
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


PAPER_DIR = os.path.join(PROJECT_ROOT, "results", "paper")
FIG_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
VIOLET = "#4a3aa7"
INK = "#0b0b0b"
INK_2 = "#52514e"
NEUTRAL = "#9a9994"
GRID = "#e6e5e1"

COLORS = {
    "GreenOps": BLUE,
    "GreenOps (transfer-unaware)": BLUE,
    "Online Threshold [12]": ORANGE,
    "Wait Awhile [17]": VIOLET,
    "Greenest Region": AQUA,
    "Temporal Green": MAGENTA,
    "Round Robin": YELLOW,
    "Cost Only": NEUTRAL,
}

MARKERS = {
    "Online Threshold [12]": "s",
    "Wait Awhile [17]": "^",
    "Greenest Region": "D",
    "Temporal Green": "v",
    "Round Robin": "P",
    "Cost Only": "X",
}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#bdbcb8",
    "axes.labelcolor": INK,
    "axes.labelsize": 7.5,
    "axes.titlesize": 8,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "legend.fontsize": 6.5,
    "legend.frameon": False,
    "lines.linewidth": 1.5,
    "lines.markersize": 4,
    "font.family": "DejaVu Sans",
    "pdf.fonttype": 42,
})

WIDTH = 3.33


def save(fig, name):

    os.makedirs(FIG_DIR, exist_ok=True)

    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"),
                    bbox_inches="tight", dpi=220)

    plt.close(fig)

    print(f"  wrote paper/figures/{name}.pdf")


def read(name):
    return pd.read_csv(os.path.join(PAPER_DIR, name))


# ============================================================
# FIG 1 - carbon vs SLA frontier
# ============================================================

def fig_frontier():

    table = read("p2_frontier_summary.csv")

    ours = table[table["policy"] == "greenops"].sort_values("carbon_weight")

    base = table[table["policy"] != "greenops"]

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 2, 2.1))

    for ax, metric, xlabel in (
        (axes[0], "sla_violation_rate_mean", "SLA violation rate (%)"),
        (axes[1], "total_cost_mean", "Cost per run (k$)"),
    ):

        scale = 1 / 1000 if metric == "total_cost_mean" else 1

        ax.plot(ours[metric] * scale, ours["total_carbon_g_mean"] / 1e6,
                color=BLUE, marker="o", zorder=3, label="GreenOps (w_c sweep)")

        for _, row in ours.iterrows():
            if row["carbon_weight"] in (0.2, 0.6, 3.0):
                ax.annotate(f"w_c={row['carbon_weight']:g}",
                            (row[metric] * scale,
                             row["total_carbon_g_mean"] / 1e6),
                            xytext=(4, 3), textcoords="offset points",
                            fontsize=6, color=BLUE)

        for _, row in base.iterrows():
            ax.scatter(row[metric] * scale, row["total_carbon_g_mean"] / 1e6,
                       color=COLORS[row["label"]],
                       marker=MARKERS[row["label"]], s=26, zorder=4,
                       edgecolor="white", linewidth=0.6, label=row["label"])

        ax.set_xlabel(xlabel)

    axes[0].set_ylabel("Carbon per run (tCO₂eq)")
    axes[0].set_title("Carbon vs. SLA violations", loc="left")
    axes[1].set_title("Carbon vs. cost", loc="left")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(handles, labels, loc="upper center", ncol=4,
               bbox_to_anchor=(0.5, 1.13))

    fig.tight_layout()

    save(fig, "fig_frontier")


# ============================================================
# FIG 2 - data gravity
# ============================================================

def fig_gravity():

    table = read("p3_gravity_summary.csv")

    labels = ["Greenest Region", "Online Threshold [12]", "Wait Awhile [17]",
              "GreenOps (transfer-unaware)", "GreenOps"]

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 2, 2.0))

    for label in labels:

        series = table[table["label"] == label].sort_values("gb_per_core_hour")

        x = series["gb_per_core_hour"].replace(0, 0.1)

        style = "--" if "unaware" in label else "-"

        axes[0].plot(x, series["total_carbon_g_mean"] / 1e6, style,
                     color=COLORS[label], marker=MARKERS.get(label, "o"),
                     label=label)

        axes[1].plot(x, series["moved_jobs_pct_mean"], style,
                     color=COLORS[label], marker=MARKERS.get(label, "o"),
                     label=label)

    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlabel("Input data per core-hour (GB, log; 0 plotted at 0.1)")

    axes[0].set_ylabel("Carbon per run (tCO₂eq)")
    axes[1].set_ylabel("Jobs moved off home region (%)")
    axes[0].set_title("Total emissions incl. transfer", loc="left")
    axes[1].set_title("Spatial shifting retreats", loc="left")

    handles, lbls = axes[0].get_legend_handles_labels()

    fig.legend(handles, lbls, loc="upper center", ncol=5,
               bbox_to_anchor=(0.5, 1.1))

    fig.tight_layout()

    save(fig, "fig_gravity")


# ============================================================
# FIG 3 - forecast error
# ============================================================

def fig_forecast():

    table = read("p4_forecast_summary.csv")

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 2, 1.9))

    for label in ("Wait Awhile [17]", "Online Threshold [12]",
                  "Greenest Region", "GreenOps"):

        series = table[table["label"] == label].sort_values("forecast_error")

        for ax, metric, scale in (
            (axes[0], "total_carbon_g_mean", 1e-6),
            (axes[1], "sla_violation_rate_mean", 1),
        ):

            if len(series) == 1:
                ax.axhline(series[metric].iloc[0] * scale,
                           color=COLORS[label], linestyle=":", linewidth=1.2,
                           label=f"{label} (no forecast)")
            else:
                ax.plot(series["forecast_error"] * 100,
                        series[metric] * scale, color=COLORS[label],
                        marker=MARKERS.get(label, "o"), label=label)

    for ax in axes:
        ax.set_xlabel("Forecast error at 24 h (%)")

    axes[0].set_ylabel("Carbon per run (tCO₂eq)")
    axes[1].set_ylabel("SLA violation rate (%)")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(handles, labels, loc="upper center", ncol=4,
               bbox_to_anchor=(0.5, 1.12))

    fig.tight_layout()

    save(fig, "fig_forecast")


# ============================================================
# FIG 4 - traces + workload
# ============================================================

def fig_setting():

    fig, axes = plt.subplots(1, 2, figsize=(WIDTH * 2, 1.7),
                             gridspec_kw=dict(width_ratios=[1.6, 1]))

    traces = load_traces("summer_2024", CORE_REGIONS)

    hours = np.arange(24 * 7)

    for name, color in (("India", AQUA), ("Germany", ORANGE),
                        ("Norway", BLUE)):

        values = traces[name][: len(hours)]

        axes[0].plot(hours / 24, values, color=color, linewidth=1.1)

        axes[0].annotate(name, (7, values[-1]), xytext=(3, 0),
                         textcoords="offset points", fontsize=6.5,
                         va="center", color=INK_2)

    axes[0].set_xlim(0, 7)
    axes[0].set_ylim(0, 800)
    axes[0].set_xlabel("Day (1-7 Jul 2024, UTC)")
    axes[0].set_ylabel("gCO₂eq/kWh")
    axes[0].set_title("Grid carbon intensity", loc="left")

    jobs = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "workload_traces",
                                    "alibaba_jobs.csv.gz"))

    per_hour = (jobs["arrival_s"] // 3600).value_counts().sort_index()

    cpu_hours = (jobs["cpu"] * jobs["runtime_s"] / 3600).groupby(
        jobs["arrival_s"] // 3600).sum()

    axes[1].plot(cpu_hours.index / 24, cpu_hours.values / 1000 * 0.1,
                 color=INK_2, linewidth=1)
    axes[1].set_xlabel("Day of trace")
    axes[1].set_ylabel("Submitted k vCPU-h / h")
    axes[1].set_title("Alibaba 2018 demand (10 %)", loc="left")

    fig.tight_layout()

    save(fig, "fig_setting")


def main():

    print("Generating paper figures ...")

    fig_setting()
    fig_frontier()
    fig_gravity()
    fig_forecast()


if __name__ == "__main__":
    main()
