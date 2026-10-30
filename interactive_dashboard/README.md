# GreenOps Interactive Cloud Dashboard

A neat, lightweight, and self-contained interactive web dashboard for real-time workload assignment and carbon-aware multi-objective scheduling.

---

## Features

- **Workload Assignment**: Interactive form with presets (Interactive API, Batch ETL, ML Training, Sovereign Workload) to specify CPU, memory, runtime, deadlines, data origin, dataset size (GB), budget cap, and carbon priority ($p_j$).
- **Live Regional Grid Signals**: Real-time visualization of 6 regions (Germany, Norway, India, France, Poland, Great Britain) with current carbon intensity (gCO2eq/kWh), electricity prices ($/core-hour), PUE, and 24-hour trace sparklines.
- **Decision Engine & Analytics**:
  - Full SimPy discrete-event simulation of the assigned job.
  - Graphical lifecycle timeline (Data Staging $\to$ Deferral/Wait $\to$ Execution vs Deadline).
  - Carbon emission reduction (% vs Round Robin) and cost delta (% vs Cost Only).
- **Multi-Scheduler Benchmarking**: Runs the exact same job side-by-side across:
  - GreenOps MOO (Weighted)
  - GreenOps Pareto (Tchebycheff Knee)
  - Greenest Region (Spatial Only)
  - Temporal Green (Forecast-Greedy)
  - Round Robin (Carbon-Agnostic)
  - Cost Only (Cheapest)
  - Wait Awhile (Wiesner et al. '21)
  - Online Threshold (Lechowicz et al. '24)
- **Candidate Evaluator Inspector**: View the raw ranked $(r, s)$ candidates scored by GreenOps to see why the winner was chosen.
- **Zero External Dependencies**: Built entirely with Python's standard library `http.server` and vanilla HTML5/CSS3/JavaScript.

---

## How to Run

1. Activate your virtual environment (if not already activated):
   ```powershell
   .\greenops_env\Scripts\Activate.ps1
   ```

2. Start the dashboard server:
   ```powershell
   python interactive_dashboard/server.py
   ```

3. Open your browser at:
   ```
   http://127.0.0.1:8080/
   ```

*(Options: use `--port 8085` to choose a custom port, or `--no-browser` to prevent automatic browser launch).*
