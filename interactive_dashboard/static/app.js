/**
 * GreenOps Interactive Dashboard Client Logic
 */

let appConfig = null;
let currentPeriod = "summer_2024";
let jobCounter = 101;

// Preset Workloads
const PRESETS = {
  interactive_api: {
    job_id: () => `API-${jobCounter++}`,
    flexibility: "strict",
    cpu_required: 4,
    memory_required: 8,
    runtime: 0.5,
    deadline: 1.0,
    home_region: "India",
    data_gb: 0,
    carbon_priority: 0.3,
    max_cost: "",
    allowed_regions: [],
  },
  batch_etl: {
    job_id: () => `ETL-${jobCounter++}`,
    flexibility: "batch",
    cpu_required: 8,
    memory_required: 16,
    runtime: 2.0,
    deadline: 6.0,
    home_region: "Germany",
    data_gb: 25,
    carbon_priority: 0.7,
    max_cost: "",
    allowed_regions: [],
  },
  ml_training: {
    job_id: () => `ML-${jobCounter++}`,
    flexibility: "flexible",
    cpu_required: 16,
    memory_required: 32,
    runtime: 4.0,
    deadline: 16.0,
    home_region: "France",
    data_gb: 80,
    carbon_priority: 0.9,
    max_cost: "",
    allowed_regions: [],
  },
  sovereign_eu: {
    job_id: () => `SOV-${jobCounter++}`,
    flexibility: "batch",
    cpu_required: 8,
    memory_required: 16,
    runtime: 2.5,
    deadline: 8.0,
    home_region: "Germany",
    data_gb: 15,
    carbon_priority: 0.8,
    max_cost: "5.00",
    allowed_regions: ["Germany", "France", "Norway"],
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  setupEventListeners();
});

async function initDashboard() {
  try {
    // 1. Fetch Config
    const cfgRes = await fetch(`/api/config?period=${currentPeriod}`);
    if (!cfgRes.ok) throw new Error("Failed to load server config");
    appConfig = await cfgRes.json();
    populateDropdowns(appConfig);
  } catch (err) {
    console.warn("Config load notice:", err);
  }

  try {
    // 2. Fetch Regions Snapshot
    await loadRegions(currentPeriod);
  } catch (err) {
    console.warn("Regions load notice:", err);
  }

  try {
    // 3. Load Session History
    await loadHistory();
  } catch (err) {
    console.warn("History load notice:", err);
  }

  // Set initial preset
  applyPreset("batch_etl");
}

function setupEventListeners() {
  // Period dropdown
  const periodSel = document.getElementById("select-period");
  if (periodSel) {
    periodSel.addEventListener("change", async (e) => {
      currentPeriod = e.target.value;
      try {
        const cfgRes = await fetch(`/api/config?period=${currentPeriod}`);
        appConfig = await cfgRes.json();
        populateDropdowns(appConfig);
      } catch (err) {
        console.error(err);
      }
      loadRegions(currentPeriod);
    });
  }

  // Carbon Priority Slider
  const prioritySlider = document.getElementById("input-priority");
  const priorityVal = document.getElementById("priority-val");
  if (prioritySlider && priorityVal) {
    prioritySlider.addEventListener("input", (e) => {
      priorityVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  // Preset chips
  document.querySelectorAll(".chip-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const presetKey = btn.getAttribute("data-preset");
      applyPreset(presetKey);
    });
  });

  // Advanced accordion toggle
  const accHeader = document.querySelector(".accordion-header");
  const accBody = document.querySelector(".accordion-body");
  if (accHeader && accBody) {
    accHeader.addEventListener("click", () => {
      const isHidden = accBody.style.display === "none";
      accBody.style.display = isHidden ? "grid" : "none";
      accHeader.querySelector(".acc-arrow").textContent = isHidden ? "▲" : "▼";
    });
    // Default closed
    accBody.style.display = "none";
  }

  // Form Submission
  const form = document.getElementById("job-form");
  if (form) {
    form.addEventListener("submit", handleJobSubmit);
  }

  // Clear History
  const clearBtn = document.getElementById("btn-clear-history");
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      await fetch("/api/clear_history", { method: "POST" });
      loadHistory();
    });
  }
}

function populateDropdowns(config) {
  if (!config) return;

  // Schedulers
  const schedSel = document.getElementById("input-scheduler");
  if (schedSel && config.schedulers) {
    const prev = schedSel.value;
    schedSel.innerHTML = "";
    config.schedulers.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.label + (s.recommended ? " (Recommended)" : "");
      if (prev ? s.id === prev : s.id === "greenops_moo") opt.selected = true;
      schedSel.appendChild(opt);
    });
  }

  // Home Region
  const homeSel = document.getElementById("input-home");
  if (homeSel && config.regions) {
    const prevHome = homeSel.value;
    homeSel.innerHTML = "";
    config.regions.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      if (prevHome ? r === prevHome : r === "Germany") opt.selected = true;
      homeSel.appendChild(opt);
    });
  }

  // Data residency checkboxes
  const pillsWrap = document.getElementById("allowed-regions-pills");
  if (pillsWrap && config.regions) {
    pillsWrap.innerHTML = "";
    config.regions.forEach((r) => {
      const label = document.createElement("label");
      label.className = "pill-check";
      label.innerHTML = `
        <input type="checkbox" name="allowed-region" value="${r}" checked />
        <span>${r}</span>
      `;
      pillsWrap.appendChild(label);
    });
  }
}

async function loadRegions(period) {
  try {
    const res = await fetch(`/api/regions?period=${period}&hour=0`);
    if (!res.ok) throw new Error("Could not load regions snapshot");
    const data = await res.json();
    renderRegions(data.regions || []);
  } catch (e) {
    console.error("Failed to load regions:", e);
  }
}

function renderRegions(regions) {
  const container = document.getElementById("regions-container");
  if (!container) return;

  container.innerHTML = "";
  regions.forEach((r) => {
    let ciClass = "ci-clean";
    if (r.current_ci > 300) ciClass = "ci-dirty";
    else if (r.current_ci > 100) ciClass = "ci-moderate";

    const card = document.createElement("div");
    card.className = "region-card";

    // Generate mini SVG sparkline
    const sparklineSvg = generateSparkline(r.trace_preview);

    card.innerHTML = `
      <div class="region-top">
        <span class="region-name">${r.name}</span>
        <span class="ci-badge ${ciClass}">${r.current_ci != null ? r.current_ci + ' g/kWh' : 'Offline'}</span>
      </div>
      <div class="region-metrics">
        <div class="region-metric-row">
          <span>Cost:</span>
          <strong>$${(r.cost_per_cpu_hour || 0).toFixed(2)}/core-h</strong>
        </div>
        <div class="region-metric-row">
          <span>Facility PUE:</span>
          <strong>${(r.pue || 1.2).toFixed(2)}</strong>
        </div>
        <div class="region-metric-row">
          <span>Pool Power:</span>
          <span>${r.idle_power_kw || 0.1}kW idle / ${r.max_power_kw || 0.5}kW peak</span>
        </div>
      </div>
      <div class="region-sparkline">${sparklineSvg}</div>
    `;
    container.appendChild(card);
  });
}

function generateSparkline(trace) {
  if (!trace || trace.length === 0) return "";
  const values = trace.map((t) => t.intensity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 180;
  const height = 24;

  const points = values.map((val, idx) => {
    const x = (idx / (values.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  return `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" style="width:100%;height:100%;overflow:visible;">
      <polyline fill="none" stroke="#3b82f6" stroke-width="2" points="${points}" opacity="0.85" />
    </svg>
  `;
}

function applyPreset(presetKey) {
  const p = PRESETS[presetKey];
  if (!p) return;

  const setVal = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  setVal("input-job-id", p.job_id());
  setVal("input-flexibility", p.flexibility);
  setVal("input-cpu", p.cpu_required);
  setVal("input-memory", p.memory_required);
  setVal("input-runtime", p.runtime);
  setVal("input-deadline", p.deadline);
  setVal("input-home", p.home_region);
  setVal("input-data-gb", p.data_gb);
  setVal("input-priority", p.carbon_priority);
  setVal("input-budget", p.max_cost);

  const priorityVal = document.getElementById("priority-val");
  if (priorityVal) priorityVal.textContent = p.carbon_priority.toFixed(2);

  // Checkboxes
  const checkboxes = document.querySelectorAll('input[name="allowed-region"]');
  checkboxes.forEach((cb) => {
    if (!p.allowed_regions || p.allowed_regions.length === 0) {
      cb.checked = true;
    } else {
      cb.checked = p.allowed_regions.includes(cb.value);
    }
  });
}

async function handleJobSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("btn-submit-job");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>⏳ Optimizing &amp; Simulating...</span>`;

  try {
    const checkedRegions = Array.from(
      document.querySelectorAll('input[name="allowed-region"]:checked')
    ).map((cb) => cb.value);

    const totalRegionsCount = appConfig?.regions?.length || 6;
    const allowed = (checkedRegions.length === 0 || checkedRegions.length === totalRegionsCount)
      ? null
      : checkedRegions;

    const payload = {
      job_id: document.getElementById("input-job-id").value || `JOB-${jobCounter++}`,
      flexibility: document.getElementById("input-flexibility").value,
      cpu_required: parseInt(document.getElementById("input-cpu").value, 10),
      memory_required: parseInt(document.getElementById("input-memory").value, 10),
      runtime: parseFloat(document.getElementById("input-runtime").value),
      deadline: parseFloat(document.getElementById("input-deadline").value),
      home_region: document.getElementById("input-home").value,
      data_gb: parseFloat(document.getElementById("input-data-gb").value || 0),
      carbon_priority: parseFloat(document.getElementById("input-priority").value),
      max_cost: document.getElementById("input-budget").value || null,
      allowed_regions: allowed,
      scheduler: document.getElementById("input-scheduler").value,
      period: currentPeriod,
      compare_all: document.getElementById("check-compare-all")?.checked ?? true,
      // Advanced weights
      carbon_weight: parseFloat(document.getElementById("input-w-carbon")?.value || 0.6),
      cost_weight: parseFloat(document.getElementById("input-w-cost")?.value || 0.2),
      waiting_weight: parseFloat(document.getElementById("input-w-sla")?.value || 0.2),
      max_wait: parseFloat(document.getElementById("input-max-wait")?.value || 12),
      risk_aversion: 0.5,
      mode: document.getElementById("input-scheduler").value === "greenops_pareto" ? "pareto" : "weighted",
    };

    const res = await fetch("/api/schedule_job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    renderDecisionResults(data);
    await loadHistory();
  } catch (err) {
    console.error("Job scheduling error:", err);
    alert("Scheduling error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<span>🚀 Assign &amp; Schedule Job</span>`;
  }
}

function renderDecisionResults(data) {
  const container = document.getElementById("results-area");
  if (!container) return;

  const res = data.result || {};
  const isRejected = res.status === "rejected";
  const isSlaViolated = res.sla_violated;
  const movedData = (res.transfer_hours || 0) > 0;

  if (isRejected) {
    container.innerHTML = `
      <div class="decision-hero" style="border-color:#f43f5e;background:rgba(244,63,94,0.1);">
        <div>
          <h2>⚠️ ${res.job_id || 'Job'} Rejected at Admission</h2>
          <div class="sub" style="color:#fb7185;">
            Reason: <strong>${res.reject_reason || 'No region satisfies locality, capacity, or budget caps.'}</strong>
          </div>
        </div>
        <div>
          <span class="status-badge status-violated">REJECTED</span>
        </div>
      </div>
      <p style="margin-top:16px;color:var(--text-secondary);font-size:13px;">
        💡 <em>Tip: Try relaxing data residency restrictions, increasing the budget, or reducing required vCPUs.</em>
      </p>
    `;
    return;
  }

  let deltaBadge = "";
  if (data.carbon_saving_pct !== null && data.carbon_saving_pct !== undefined) {
    const isGood = data.carbon_saving_pct >= 0;
    deltaBadge = `<span class="${isGood ? 'delta-good' : 'delta-bad'}">${isGood ? '−' : '+'}${Math.abs(data.carbon_saving_pct)}% vs Round Robin</span>`;
  }

  let costDeltaBadge = "";
  if (data.cost_overhead_pct !== null && data.cost_overhead_pct !== undefined) {
    costDeltaBadge = `<span class="delta-neutral">+${data.cost_overhead_pct}% vs Cost Only</span>`;
  }

  const startTimeVal = res.start_time != null ? res.start_time : 0.0;
  const finishTimeVal = res.finish_time != null ? res.finish_time : (startTimeVal + (res.runtime || 1.0));
  const deadlineVal = res.deadline != null ? res.deadline : finishTimeVal;
  const totalSpan = Math.max(deadlineVal, finishTimeVal) || 1.0;

  const stagingPct = ((res.transfer_hours || 0) / totalSpan) * 100;
  const waitPct = (Math.max(0, (startTimeVal - ((res.arrival_time || 0) + (res.transfer_hours || 0)))) / totalSpan) * 100;
  const execPct = ((res.runtime || 1.0) / totalSpan) * 100;

  // Build Comparison Rows
  let compRows = "";
  if (data.comparison && data.comparison.length > 0) {
    compRows = data.comparison.map((c) => {
      const activeCls = c.is_active ? "active-policy" : "";
      const slaLabel = c.sla_violated
        ? `<span style="color:#fb7185;font-weight:600;">VIOLATED</span>`
        : `<span style="color:#34d399;font-weight:600;">MET</span>`;
      const startStr = c.start_time != null ? `${c.start_time.toFixed(2)}h` : "—";
      const waitStr = c.waiting_time != null ? `${c.waiting_time.toFixed(2)}h` : "—";
      const carbonStr = c.carbon_emitted != null ? `${c.carbon_emitted.toFixed(1)} g` : "—";
      const costStr = c.cost != null ? `$${c.cost.toFixed(2)}` : "—";

      return `
        <tr class="${activeCls}">
          <td><strong>${c.label}</strong> ${c.is_active ? '(Selected)' : ''}</td>
          <td>${c.region || 'None'}</td>
          <td class="num-cell">${startStr}</td>
          <td class="num-cell">${waitStr}</td>
          <td class="num-cell"><strong>${carbonStr}</strong></td>
          <td class="num-cell">${costStr}</td>
          <td>${slaLabel}</td>
        </tr>
      `;
    }).join("");
  }

  // Build Candidates Rows
  let candidateRows = "";
  if (data.candidates && data.candidates.length > 0) {
    candidateRows = data.candidates.slice(0, 8).map((c, idx) => {
      return `
        <tr>
          <td>#${idx + 1} ${c.region}</td>
          <td class="num-cell">t=${(c.start_time || 0).toFixed(1)}h</td>
          <td class="num-cell">${(c.waiting_time || 0).toFixed(1)}h</td>
          <td class="num-cell">${(c.carbon || 0).toFixed(1)} g</td>
          <td class="num-cell">${(c.carbon_adjusted || 0).toFixed(1)} g</td>
          <td class="num-cell">$${(c.cost || 0).toFixed(2)}</td>
          <td class="num-cell">${((c.sla_risk || 0) * 100).toFixed(1)}%</td>
          <td class="num-cell"><strong>${(c.score || 0).toFixed(4)}</strong></td>
        </tr>
      `;
    }).join("");
  }

  const slackLeft = (deadlineVal - finishTimeVal).toFixed(1);

  container.innerHTML = `
    <!-- Top Hero Decision Banner -->
    <div class="decision-hero">
      <div>
        <h2>${res.job_id} Assigned to ${res.region || 'Region'}</h2>
        <div class="sub">
          Flexibility: <strong>${(res.flexibility || 'batch').toUpperCase()}</strong> &middot;
          Start: <strong>t = ${startTimeVal.toFixed(2)} h</strong> &middot;
          Finish: <strong>t = ${finishTimeVal.toFixed(2)} h</strong> (Deadline: ${deadlineVal.toFixed(1)}h)
        </div>
      </div>
      <div>
        <span class="status-badge ${isSlaViolated ? 'status-violated' : 'status-on-time'}">
          ${isSlaViolated ? '⚠️ SLA VIOLATED' : '✓ SLA SATISFIED'}
        </span>
      </div>
    </div>

    <!-- 4 Metric Cards -->
    <div class="metrics-row">
      <div class="metric-card">
        <span class="metric-title">Carbon Emitted</span>
        <span class="metric-value">${(res.carbon_emitted || 0).toFixed(1)} <small style="font-size:13px;">gCO₂</small></span>
        <div class="metric-delta">${deltaBadge}</div>
      </div>
      <div class="metric-card">
        <span class="metric-title">Total Cost</span>
        <span class="metric-value">$${(res.cost || 0).toFixed(2)}</span>
        <div class="metric-delta">${costDeltaBadge}</div>
      </div>
      <div class="metric-card">
        <span class="metric-title">Deferral / Slack</span>
        <span class="metric-value">${(res.waiting_time || 0).toFixed(2)} <small style="font-size:13px;">h wait</small></span>
        <div class="metric-delta delta-neutral">Slack left: ${slackLeft}h</div>
      </div>
      <div class="metric-card">
        <span class="metric-title">Data Movement</span>
        <span class="metric-value">${res.data_gb || 0} <small style="font-size:13px;">GB</small></span>
        <div class="metric-delta ${movedData ? 'delta-neutral' : 'delta-good'}">
          ${movedData ? `Staged in ${(res.transfer_hours || 0).toFixed(2)}h ($${(res.transfer_cost || 0).toFixed(2)})` : 'Local (0 GB transfer)'}
        </div>
      </div>
    </div>

    <!-- Visual Gantt Timeline -->
    <div class="timeline-card">
      <div class="timeline-header">
        <strong style="font-size:13px;">Lifecycle Timeline (Arrival to Deadline)</strong>
        <span style="font-size:12px;color:var(--text-secondary);">Total span: ${totalSpan.toFixed(1)}h</span>
      </div>
      <div class="timeline-bar-wrapper">
        ${stagingPct > 0 ? `<div class="timeline-segment seg-staging" style="width:${stagingPct}%;" title="Data Staging: ${(res.transfer_hours || 0).toFixed(2)}h">Staging</div>` : ''}
        ${waitPct > 0 ? `<div class="timeline-segment seg-waiting" style="width:${waitPct}%;" title="Deferred: ${(res.waiting_time || 0).toFixed(2)}h">Wait ${(res.waiting_time || 0).toFixed(1)}h</div>` : ''}
        <div class="timeline-segment seg-execution" style="width:${execPct}%;" title="Compute: ${(res.runtime || 0).toFixed(1)}h in ${res.region}">Run in ${res.region}</div>
      </div>
      <div class="timeline-legend">
        ${stagingPct > 0 ? '<div class="legend-item"><div class="legend-color seg-staging"></div><span>WAN Data Staging</span></div>' : ''}
        ${waitPct > 0 ? '<div class="legend-item"><div class="legend-color seg-waiting"></div><span>Temporal Deferral</span></div>' : ''}
        <div class="legend-item"><div class="legend-color seg-execution"></div><span>Compute Execution</span></div>
      </div>
    </div>

    <!-- Schedulers Comparison Table -->
    ${compRows ? `
      <div>
        <div class="section-header" style="margin-top:8px;">
          <h3 class="section-title">⚖️ Multi-Scheduler Comparison (Same Workload)</h3>
        </div>
        <div class="comparison-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Policy</th>
                <th>Region</th>
                <th class="num-cell">Start Time</th>
                <th class="num-cell">Wait</th>
                <th class="num-cell">Carbon</th>
                <th class="num-cell">Cost</th>
                <th>SLA</th>
              </tr>
            </thead>
            <tbody>${compRows}</tbody>
          </table>
        </div>
      </div>
    ` : ''}

    <!-- Candidate Evaluations Inspector -->
    ${candidateRows ? `
      <div>
        <div class="section-header" style="margin-top:8px;">
          <h3 class="section-title">🔍 Evaluated Candidates (r, s) Ranked by GreenOps</h3>
        </div>
        <div class="comparison-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th class="num-cell">Start</th>
                <th class="num-cell">Wait</th>
                <th class="num-cell">Est. Carbon</th>
                <th class="num-cell">Adj. Carbon</th>
                <th class="num-cell">Cost</th>
                <th class="num-cell">SLA Risk</th>
                <th class="num-cell">MOO Score</th>
              </tr>
            </thead>
            <tbody>${candidateRows}</tbody>
          </table>
        </div>
      </div>
    ` : ''}
  `;
}

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const data = await res.json();
    renderHistoryTable(data.history || []);
  } catch (e) {
    console.error("Failed to load history:", e);
  }
}

function renderHistoryTable(history) {
  const tbody = document.getElementById("history-tbody");
  if (!tbody) return;

  if (history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:24px;">No jobs assigned in this session yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = history.map((j) => {
    const slaBadge = j.sla_violated
      ? `<span style="color:#fb7185;font-weight:600;">VIOLATED</span>`
      : `<span style="color:#34d399;font-weight:600;">MET</span>`;
    return `
      <tr>
        <td><strong>${j.job_id}</strong></td>
        <td>${j.scheduler}</td>
        <td><span class="ci-badge ci-clean">${j.region}</span></td>
        <td>${j.cpu} cores / ${j.runtime}h</td>
        <td class="num-cell">${(j.waiting_time || 0).toFixed(2)}h</td>
        <td class="num-cell"><strong>${(j.carbon_emitted || 0).toFixed(1)} g</strong></td>
        <td class="num-cell">$${(j.cost || 0).toFixed(2)}</td>
        <td>${slaBadge}</td>
      </tr>
    `;
  }).join("");
}
