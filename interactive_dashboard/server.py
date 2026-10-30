"""
GreenOps Interactive Cloud Dashboard Server
===========================================
A robust, threaded, self-contained local web server providing an interactive UI
for assigning, scheduling, and comparing cloud workloads across geo-distributed
regions using GreenOps MOO and baseline scheduling algorithms.

Usage:
    python interactive_dashboard/server.py
    python interactive_dashboard/server.py --port 8080 --no-browser
"""

import argparse
import http.server
import json
import os
import sys
import threading
import urllib.parse
import webbrowser

# Ensure the project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenario import (
    CORE_REGIONS,
    EXTENDED_REGIONS,
    PERIODS,
    REGION_PROFILES,
    build_regions,
    load_traces,
    make_scheduler,
)
from sim.job import Job
from sim.region import Region
from sim.engine import CloudSimulator
from sim.forecast import CarbonForecaster, REALISTIC_ERROR
from sim.network import NetworkModel
from metrics.collector import MetricsCollector

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")

# Global in-memory caches and job history
JOB_HISTORY = []
HISTORY_LOCK = threading.Lock()
_TRACE_CACHE = {}


def get_region_names_for_period(period):
    """Return available regions for the chosen period."""
    if period == "controlled":
        return CORE_REGIONS
    return EXTENDED_REGIONS


def get_cached_traces(period, region_names):
    """Cache loaded carbon traces in memory to avoid repeated disk reads."""
    key = (period, tuple(sorted(region_names)))
    if key not in _TRACE_CACHE:
        _TRACE_CACHE[key] = load_traces(period, region_names)
    return _TRACE_CACHE[key]


def safe_num(val, digits=2, default=0.0):
    """Safely convert and round a numeric value."""
    if val is None:
        return default
    try:
        return round(float(val), digits)
    except (TypeError, ValueError):
        return default


def get_region_snapshot(period="summer_2024", hour=0.0):
    """Return metadata and current carbon intensity for all active regions."""
    region_names = get_region_names_for_period(period)
    traces = get_cached_traces(period, region_names)
    regions = build_regions(traces)
    snapshot = []

    for r in regions:
        profile = REGION_PROFILES.get(r.name, {})
        current_ci = r.get_carbon_intensity(hour)
        # Next 24 hours trace preview
        preview_hours = []
        for h in range(24):
            preview_hours.append({
                "hour": h,
                "intensity": safe_num(r.get_carbon_intensity(hour + h), 1, 0.0)
            })

        snapshot.append({
            "name": r.name,
            "current_ci": safe_num(current_ci, 1, None),
            "cost_per_cpu_hour": safe_num(r.cost_per_cpu_hour, 2, 0.10),
            "cpu_capacity": r.cpu_capacity,
            "idle_power_kw": safe_num(r.idle_power_kw, 2, 0.10),
            "max_power_kw": safe_num(r.max_power_kw, 2, 0.50),
            "pue": safe_num(r.pue, 2, 1.30),
            "trace_preview": preview_hours,
        })
    return snapshot


def run_single_job_simulation(scheduler_key, job_params, period="summer_2024",
                             forecast_error=REALISTIC_ERROR, moo_params=None):
    """Run a single job through a full SimPy discrete-event simulation."""
    region_names = get_region_names_for_period(period)
    traces = get_cached_traces(period, region_names)
    regions = build_regions(traces, cpu_capacity=64)
    forecaster = CarbonForecaster(regions, error_level=forecast_error, seed=42)
    network = NetworkModel()

    # Build scheduler
    kwargs = {}
    if scheduler_key.startswith("greenops"):
        kwargs.update(moo_params or {})
    if "max_wait" in (moo_params or {}):
        kwargs["max_wait"] = moo_params["max_wait"]

    scheduler = make_scheduler(scheduler_key, **kwargs)
    metrics = MetricsCollector()
    sim = CloudSimulator(regions, scheduler, metrics, forecaster, network, verbose=False)

    # Filter allowed regions to match active period
    req_allowed = job_params.get("allowed_regions")
    allowed_regions = None
    if req_allowed:
        allowed_regions = [r for r in req_allowed if r in region_names] or None

    # Handle home region
    home_region = job_params.get("home_region")
    if home_region not in region_names:
        home_region = region_names[0]

    # Instantiate Job
    job = Job(
        job_id=str(job_params.get("job_id", "JOB-1")),
        arrival_time=float(job_params.get("arrival_time", 0.0)),
        cpu_required=int(job_params.get("cpu_required", 4)),
        memory_required=int(job_params.get("memory_required", 8)),
        runtime=float(job_params.get("runtime", 2.0)),
        deadline=float(job_params.get("deadline", 8.0)),
        flexibility=str(job_params.get("flexibility", "flexible")),
        max_cost=float(job_params["max_cost"]) if job_params.get("max_cost") not in (None, "", "null") else None,
        carbon_priority=float(job_params.get("carbon_priority", 0.5)),
        allowed_regions=allowed_regions,
        home_region=home_region,
        data_gb=float(job_params.get("data_gb", 0.0)),
    )

    # Capture candidate evaluations if GreenOps
    candidates_data = []
    if hasattr(scheduler, "generate_candidates"):
        scheduler.bind(regions, forecaster, network)
        raw_candidates = scheduler.generate_candidates(job, regions, job.arrival_time)
        scored_candidates = scheduler.score_candidates(raw_candidates, job)
        for c in scored_candidates:
            candidates_data.append({
                "region": c["region"].name,
                "start_time": safe_num(c["start_time"], 2),
                "waiting_time": safe_num(c["waiting_time"], 2),
                "finish_time": safe_num(c["finish_time"], 2),
                "carbon": safe_num(c["carbon"], 1),
                "carbon_adjusted": safe_num(c["carbon_adjusted"], 1),
                "cost": safe_num(c["cost"], 2),
                "sla_risk": safe_num(c["sla_risk"], 4),
                "score": safe_num(c.get("score", 0.0), 4),
            })
        candidates_data.sort(key=lambda x: x["score"])

    # Run simulation
    sim.submit_job(job)
    sim.run()

    res_list = metrics.get_results()
    if not res_list:
        return {
            "result": {
                "job_id": job.job_id,
                "status": "rejected",
                "region": "None",
                "sla_violated": True,
                "carbon_emitted": 0.0,
                "cost": 0.0,
                "waiting_time": 0.0,
                "start_time": None,
                "finish_time": None,
                "reject_reason": "No region satisfies locality, capacity or budget constraints."
            },
            "candidates": candidates_data,
        }

    res = res_list[0]
    return {
        "result": res,
        "candidates": candidates_data,
    }


class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Custom HTTP handler serving dashboard API and static assets with thread safety."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # ---------------- Static Files ----------------
        if path in ("/", "/index.html"):
            if not os.path.exists(HTML_FILE):
                self.send_error(404, "index.html not found")
                return
            with open(HTML_FILE, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
            return

        if path.startswith("/static/"):
            rel_file = path[len("/static/"):].replace("/", os.sep)
            file_path = os.path.join(STATIC_DIR, rel_file)
            if not os.path.exists(file_path) or os.path.isdir(file_path):
                self.send_error(404, "Static file not found")
                return

            ctype = "text/plain"
            if file_path.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            elif file_path.endswith(".js"):
                ctype = "application/javascript; charset=utf-8"
            elif file_path.endswith(".svg"):
                ctype = "image/svg+xml"
            elif file_path.endswith(".png"):
                ctype = "image/png"

            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(content)
            return

        # ---------------- API Endpoints ----------------
        if path == "/api/config":
            period = query.get("period", ["summer_2024"])[0]
            active_regions = list(get_region_names_for_period(period))

            self.send_json({
                "regions": active_regions,
                "core_regions": list(CORE_REGIONS),
                "periods": [
                    {"id": "summer_2024", "label": "Summer 2024 (Solar High)", "default": True},
                    {"id": "winter_2024", "label": "Winter 2024 (Wind High)"},
                    {"id": "controlled", "label": "Controlled 24h Profile (India, Germany, Norway)"},
                ],
                "schedulers": [
                    {"id": "greenops_moo", "label": "GreenOps MOO (Weighted)", "recommended": True},
                    {"id": "greenops_pareto", "label": "GreenOps Pareto (Knee)"},
                    {"id": "greenest_region", "label": "Greenest Region (Spatial Only)"},
                    {"id": "temporal_green", "label": "Temporal Green (Forecast-Greedy)"},
                    {"id": "round_robin", "label": "Round Robin (Carbon-Agnostic)"},
                    {"id": "cost_only", "label": "Cost Only (Cheapest)"},
                    {"id": "wait_awhile", "label": "Wait Awhile [Wiesner '21]"},
                    {"id": "threshold", "label": "Online Threshold [Lechowicz '24]"},
                ],
                "defaults": {
                    "period": "summer_2024",
                    "forecast_error": 0.15,
                    "carbon_weight": 0.6,
                    "cost_weight": 0.2,
                    "waiting_weight": 0.2,
                    "risk_aversion": 0.5,
                    "max_wait": 12,
                }
            })
            return

        if path == "/api/regions":
            period = query.get("period", ["summer_2024"])[0]
            hour = float(query.get("hour", [0.0])[0])
            snapshot = get_region_snapshot(period=period, hour=hour)
            self.send_json({"period": period, "hour": hour, "regions": snapshot})
            return

        if path == "/api/history":
            with HISTORY_LOCK:
                history_copy = list(JOB_HISTORY)
            self.send_json({"history": history_copy})
            return

        self.send_error(404, "API endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body) if body else {}

        if path == "/api/schedule_job":
            period = data.get("period", "summer_2024")
            forecast_error = float(data.get("forecast_error", 0.15))
            chosen_scheduler = data.get("scheduler", "greenops_moo")
            compare_all = bool(data.get("compare_all", True))

            moo_params = {
                "carbon_weight": float(data.get("carbon_weight", 0.6)),
                "cost_weight": float(data.get("cost_weight", 0.2)),
                "waiting_weight": float(data.get("waiting_weight", 0.2)),
                "risk_aversion": float(data.get("risk_aversion", 0.5)),
                "max_wait": float(data.get("max_wait", 12)),
                "mode": data.get("mode", "weighted"),
            }

            # 1. Primary Run
            primary_out = run_single_job_simulation(
                chosen_scheduler, data, period=period,
                forecast_error=forecast_error, moo_params=moo_params
            )

            primary_res = primary_out.get("result", {})
            candidates = primary_out.get("candidates", [])

            # Compute timeline intervals safely
            timeline = []
            if primary_res.get("status") == "completed" and primary_res.get("start_time") is not None:
                arrival = safe_num(primary_res.get("arrival_time"), 2, 0.0)
                transfer_hours = safe_num(primary_res.get("transfer_hours"), 2, 0.0)
                start_time = safe_num(primary_res.get("start_time"), 2, 0.0)
                runtime = safe_num(primary_res.get("runtime"), 2, 1.0)
                finish_time = safe_num(primary_res.get("finish_time"), 2, start_time + runtime)
                deadline = safe_num(primary_res.get("deadline"), 2, finish_time)

                timeline.append({"name": "Arrival", "start": arrival, "end": arrival, "type": "event"})
                if transfer_hours > 0:
                    timeline.append({
                        "name": f"Staging Data ({safe_num(primary_res.get('data_gb'), 0)} GB)",
                        "start": arrival,
                        "end": arrival + transfer_hours,
                        "type": "staging"
                    })
                if start_time > arrival + transfer_hours + 1e-4:
                    timeline.append({
                        "name": f"Deferred / Waiting ({start_time - (arrival + transfer_hours):.1f}h)",
                        "start": arrival + transfer_hours,
                        "end": start_time,
                        "type": "waiting"
                    })
                timeline.append({
                    "name": f"Compute Execution in {primary_res.get('region', 'Region')}",
                    "start": start_time,
                    "end": finish_time,
                    "type": "execution"
                })
                timeline.append({"name": "SLA Deadline", "start": deadline, "end": deadline, "type": "deadline"})

            # 2. Comparison across all 7 policies (if requested)
            comparison = []
            if compare_all:
                policies_to_compare = [
                    ("round_robin", "Round Robin"),
                    ("cost_only", "Cost Only"),
                    ("greenest_region", "Greenest Region"),
                    ("temporal_green", "Temporal Green"),
                    ("wait_awhile", "Wait Awhile"),
                    ("threshold", "Online Threshold"),
                    ("greenops_moo", "GreenOps MOO"),
                ]

                for p_key, p_label in policies_to_compare:
                    try:
                        p_out = run_single_job_simulation(
                            p_key, data, period=period,
                            forecast_error=forecast_error, moo_params=moo_params
                        )
                        p_res = p_out.get("result", {})
                        if p_res:
                            comparison.append({
                                "key": p_key,
                                "label": p_label,
                                "region": p_res.get("region") or "None",
                                "start_time": safe_num(p_res.get("start_time"), 2, None),
                                "waiting_time": safe_num(p_res.get("waiting_time"), 2, 0.0),
                                "finish_time": safe_num(p_res.get("finish_time"), 2, None),
                                "carbon_emitted": safe_num(p_res.get("carbon_emitted"), 1, 0.0),
                                "cost": safe_num(p_res.get("cost"), 2, 0.0),
                                "sla_violated": bool(p_res.get("sla_violated", False)),
                                "is_active": (p_key == chosen_scheduler)
                            })
                    except Exception as e:
                        comparison.append({"key": p_key, "label": p_label, "error": str(e), "is_active": False})

            # 3. Baseline Deltas
            rr_entry = next((c for c in comparison if c.get("key") == "round_robin" and "carbon_emitted" in c), None)
            co_entry = next((c for c in comparison if c.get("key") == "cost_only" and "cost" in c), None)

            carbon_saving_vs_rr = None
            if rr_entry and rr_entry["carbon_emitted"] > 0 and primary_res.get("carbon_emitted"):
                diff = rr_entry["carbon_emitted"] - primary_res["carbon_emitted"]
                carbon_saving_vs_rr = safe_num((diff / rr_entry["carbon_emitted"]) * 100, 1)

            cost_overhead_vs_co = None
            if co_entry and co_entry["cost"] > 0 and primary_res.get("cost"):
                diff = primary_res["cost"] - co_entry["cost"]
                cost_overhead_vs_co = safe_num((diff / co_entry["cost"]) * 100, 1)

            response_data = {
                "scheduler": chosen_scheduler,
                "result": primary_res,
                "timeline": timeline,
                "candidates": candidates,
                "comparison": comparison,
                "carbon_saving_pct": carbon_saving_vs_rr,
                "cost_overhead_pct": cost_overhead_vs_co,
            }

            # Save to session history
            with HISTORY_LOCK:
                JOB_HISTORY.insert(0, {
                    "job_id": primary_res.get("job_id", data.get("job_id", "JOB")),
                    "scheduler": chosen_scheduler,
                    "region": primary_res.get("region") or "Rejected",
                    "cpu": data.get("cpu_required"),
                    "runtime": data.get("runtime"),
                    "deadline": data.get("deadline"),
                    "flexibility": data.get("flexibility"),
                    "home_region": data.get("home_region"),
                    "data_gb": data.get("data_gb"),
                    "carbon_emitted": safe_num(primary_res.get("carbon_emitted"), 1, 0.0),
                    "cost": safe_num(primary_res.get("cost"), 2, 0.0),
                    "sla_violated": bool(primary_res.get("sla_violated", False)),
                    "waiting_time": safe_num(primary_res.get("waiting_time"), 2, 0.0),
                })
                if len(JOB_HISTORY) > 50:
                    JOB_HISTORY.pop()

            self.send_json(response_data)
            return

        if path == "/api/clear_history":
            with HISTORY_LOCK:
                JOB_HISTORY.clear()
            self.send_json({"status": "cleared"})
            return

        self.send_error(404, "API endpoint not found")


def start_server(port=PORT, open_browser=True):
    """Start the Threaded HTTP server on the designated port."""
    handler = DashboardRequestHandler
    http.server.ThreadingHTTPServer.allow_reuse_address = True

    try:
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError:
        port = port + 1
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}/"
    print("=" * 68)
    print(f"  GREENOPS INTERACTIVE CLOUD DASHBOARD (THREADED)")
    print(f"  Server listening at: {url}")
    print(f"  Press Ctrl+C to terminate the dashboard server.")
    print("=" * 68)

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GreenOps Interactive Dashboard Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Server port (default: {PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    args = parser.parse_args()

    start_server(port=args.port, open_browser=not args.no_browser)
