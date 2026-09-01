import React, { useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  BarChart3,
  Bell,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  CircleGauge,
  Clock3,
  Cpu,
  FileSpreadsheet,
  Gauge,
  Info,
  Layers3,
  Menu,
  Plane,
  RefreshCw,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Thermometer,
  Upload,
  Wrench,
  X,
  Zap
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const statusOrder = { CRITICAL: 0, WARNING: 1, NORMAL: 2, UNKNOWN: 3 };

function normalizeStatus(value) {
  return String(value || "UNKNOWN").toUpperCase();
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits
  });
}

function statusColor(status) {
  const s = normalizeStatus(status);
  if (s === "CRITICAL") return "critical";
  if (s === "WARNING") return "warning";
  if (s === "NORMAL") return "normal";
  return "unknown";
}

function StatusBadge({ status }) {
  const s = normalizeStatus(status);
  const Icon = s === "CRITICAL" ? ShieldAlert : s === "WARNING" ? AlertTriangle : CheckCircle2;
  return (
    <span className={`status-badge ${statusColor(s)}`}>
      <Icon size={13} />
      {s}
    </span>
  );
}

function MetricCard({ icon: Icon, label, value, sub, tone = "" }) {
  return (
    <div className={`metric-card ${tone}`}>
      <div className="metric-icon"><Icon size={19} /></div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{sub}</small>
      </div>
    </div>
  );
}

function RiskRing({ risk }) {
  const safeRisk = Math.max(0, Math.min(100, Number(risk) || 0));
  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const dash = (safeRisk / 100) * circumference;

  return (
    <div className="risk-ring-wrap">
      <svg className="risk-ring" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} className="risk-track" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          className="risk-progress"
          strokeDasharray={`${dash} ${circumference - dash}`}
        />
      </svg>
      <div className="risk-center">
        <strong>{formatNumber(safeRisk, 1)}%</strong>
        <span>risk score</span>
      </div>
    </div>
  );
}

function ParameterCard({ item, onOpen }) {
  const status = normalizeStatus(item.manual_status);
  const a = item.analytics || {};
  const maintenance = item.maintenance || {};
  const range = item.normal_range;
  const latest = Number(a.latest_value);
  const mean = Number(a.historical?.mean);
  const z = Number(a.z_score);
  const trendUp = String(a.trend || "").toUpperCase() === "INCREASING";

  return (
    <button className={`parameter-card ${statusColor(status)}`} onClick={() => onOpen(item)}>
      <div className="parameter-top">
        <div>
          <span className="parameter-name">{item.display_name || item.parameter}</span>
          <span className="parameter-key">{item.parameter}</span>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="parameter-reading">
        <strong>{formatNumber(latest, 1)}</strong>
        <span>{item.unit || ""}</span>
      </div>

      <div className="range-row">
        <span>Normal range</span>
        <b>
          {Array.isArray(range)
            ? `${formatNumber(range[0], 1)} – ${formatNumber(range[1], 1)} ${item.unit || ""}`
            : "Not defined"}
        </b>
      </div>

      <div className="parameter-mini-stats">
        <span>Z {Number.isFinite(z) ? `${z >= 0 ? "+" : ""}${z.toFixed(2)}` : "—"}</span>
        <span className={trendUp ? "trend-up" : "trend-down"}>
          {trendUp ? <ArrowUp size={13} /> : <ArrowDown size={13} />}
          {a.trend || "—"}
        </span>
        <span>Mean {formatNumber(mean, 1)}</span>
      </div>

      {maintenance.maintenance_required && (
        <div className="maintenance-line">
          <Wrench size={14} />
          <span>{maintenance.recommended_action || "Maintenance inspection required"}</span>
        </div>
      )}

      <div className="card-footer">
        <span>{maintenance.confidence || "—"} confidence</span>
        <span>Details <ChevronRight size={14} /></span>
      </div>
    </button>
  );
}

function DetailDrawer({ item, onClose }) {
  if (!item) return null;

  const a = item.analytics || {};
  const h = a.historical || {};
  const m = item.maintenance || {};
  const failures = Array.isArray(m.failure_modes) ? m.failure_modes : [];

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="detail-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="eyebrow">PARAMETER INTELLIGENCE</span>
            <h2>{item.display_name || item.parameter}</h2>
            <p>{item.parameter}</p>
          </div>
          <button className="icon-button" onClick={onClose}><X size={19} /></button>
        </div>

        <div className="drawer-reading">
          <div>
            <span>Current reading</span>
            <strong>{formatNumber(a.latest_value, 2)} <small>{item.unit || ""}</small></strong>
          </div>
          <StatusBadge status={item.manual_status} />
        </div>

        <section className="drawer-section">
          <div className="section-title"><Gauge size={16} /> Operating limits</div>
          <div className="limit-box">
            <div><span>Normal</span><strong>
              {Array.isArray(item.normal_range)
                ? `${formatNumber(item.normal_range[0], 1)} – ${formatNumber(item.normal_range[1], 1)}`
                : "Not available"}
            </strong></div>
            <div><span>Manual status</span><strong>{item.manual_status || "UNKNOWN"}</strong></div>
          </div>
        </section>

        <section className="drawer-section">
          <div className="section-title"><BarChart3 size={16} /> Analytics</div>
          <div className="analytics-grid">
            <div><span>Mean</span><b>{formatNumber(h.mean, 2)}</b></div>
            <div><span>Median</span><b>{formatNumber(h.median, 2)}</b></div>
            <div><span>Std. dev.</span><b>{formatNumber(h.std, 2)}</b></div>
            <div><span>Z-score</span><b>{formatNumber(a.z_score, 2)}</b></div>
            <div><span>Difference</span><b>{formatNumber(a.difference_from_mean, 2)}</b></div>
            <div><span>Trend</span><b>{a.trend || "—"}</b></div>
          </div>
        </section>

        <section className="drawer-section">
          <div className="section-title"><Wrench size={16} /> Maintenance intelligence</div>
          <div className="action-box">
            <div className="action-title">
              <span>Recommended action</span>
              <span className={`priority-pill ${statusColor(m.priority)}`}>{m.priority || "LOW"}</span>
            </div>
            <p>{m.recommended_action || "No maintenance action required."}</p>
          </div>
          <div className="reason-box">
            <Info size={15} />
            <p>{m.reasoning || "No additional reasoning provided."}</p>
          </div>
        </section>

        {failures.length > 0 && (
          <section className="drawer-section">
            <div className="section-title"><AlertCircle size={16} /> Related failure modes</div>
            <div className="failure-list">
              {failures.map((f, idx) => {
                const name = typeof f === "string" ? f : f.name;
                const severity = typeof f === "string" ? null : f.severity;
                return (
                  <div className="failure-item" key={`${name}-${idx}`}>
                    <div>
                      <strong>{name}</strong>
                      {severity && <small>{severity}</small>}
                    </div>
                    {typeof f !== "string" && f.source && <span>{f.source}</span>}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        <section className="drawer-section">
          <div className="section-title"><BookOpen size={16} /> Manual evidence</div>
          {item.manual_evidence_available ? (
            <div className="evidence-card">
              <div className="evidence-icon"><BookOpen size={18} /></div>
              <div>
                <strong>Maintenance manual evidence available</strong>
                <p>Use the cited manual sections in your RAG layer to inspect the source evidence for this recommendation.</p>
              </div>
            </div>
          ) : (
            <div className="empty-evidence">No maintenance-manual evidence is available for this parameter.</div>
          )}
        </section>
      </aside>
    </div>
  );
}

function UploadScreen({ aircraftId, setAircraftId, file, setFile, onAnalyze, loading, error }) {
  return (
    <div className="upload-shell">
      <div className="upload-glow glow-one" />
      <div className="upload-glow glow-two" />
      <div className="upload-card">
        <div className="brand-mark"><Plane size={25} /></div>
        <span className="eyebrow">AIRCRAFT MAINTENANCE INTELLIGENCE</span>
        <h1>Turn flight data into<br /><em>maintenance decisions.</em></h1>
        <p>
          Upload your maintenance dataset and select an aircraft. The FastAPI pipeline
          will run analytics, maintenance-manual retrieval, reranking and AI recommendations.
        </p>

        <div className="upload-form">
          <label>
            <span>Aircraft ID</span>
            <input
              value={aircraftId}
              onChange={(e) => setAircraftId(e.target.value)}
              placeholder="e.g. AIR-001"
            />
          </label>

          <label className="file-drop">
            <span>Maintenance dataset</span>
            <div className="file-drop-inner">
              <Upload size={22} />
              <div>
                <strong>{file ? file.name : "Choose Excel workbook"}</strong>
                <small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : ".xlsx or .xls"}</small>
              </div>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </label>

          {error && <div className="error-banner"><AlertCircle size={16} />{error}</div>}

          <button className="primary-button large" onClick={onAnalyze} disabled={loading || !file || !aircraftId.trim()}>
            {loading ? <><RefreshCw size={17} className="spin" /> Running intelligence pipeline...</> : <><Sparkles size={17} /> Analyze aircraft</>}
          </button>
        </div>

        <div className="upload-foot">
          <span><ShieldAlert size={14} /> Manual-grounded</span>
          <span><Activity size={14} /> Statistical analytics</span>
          <span><Cpu size={14} /> LLM recommendations</span>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [aircraftId, setAircraftId] = useState("AIR-001");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("overview");

  function navigateTo(section) {
    setActiveSection(section);
    setSidebarOpen(false);

    const targetId = {
      overview: "overview-section",
      live: "parameters-section",
      maintenance: "maintenance-section",
      evidence: "evidence-section"
    }[section];

    if (targetId) {
      requestAnimationFrame(() => {
        document.getElementById(targetId)?.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
      });
    }
  }

  async function analyze() {
    setLoading(true);
    setError("");

    try {
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(
        `${API_BASE}/api/v1/aircraft/${encodeURIComponent(aircraftId.trim())}/analysis`,
        { method: "POST", body }
      );

      const data = await response.json();

      if (!response.ok) {
        const detail = typeof data.detail === "string"
          ? data.detail
          : data.detail?.message || "Analysis request failed.";
        throw new Error(detail);
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the FastAPI backend.");
    } finally {
      setLoading(false);
    }
  }

  const parameters = result?.parameters || [];
  const aircraft = result?.aircraft || {};

  const counts = useMemo(() => {
    return parameters.reduce((acc, item) => {
      const status = normalizeStatus(item.manual_status);
      acc[status] = (acc[status] || 0) + 1;
      if (item.maintenance?.maintenance_required) acc.maintenance += 1;
      return acc;
    }, { CRITICAL: 0, WARNING: 0, NORMAL: 0, UNKNOWN: 0, maintenance: 0 });
  }, [parameters]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return [...parameters]
      .filter((p) => filter === "ALL" || normalizeStatus(p.manual_status) === filter)
      .filter((p) => {
        if (!q) return true;
        return `${p.parameter} ${p.display_name} ${p.maintenance?.recommended_action || ""}`
          .toLowerCase()
          .includes(q);
      })
      .sort((a, b) => {
        const sa = statusOrder[normalizeStatus(a.manual_status)] ?? 9;
        const sb = statusOrder[normalizeStatus(b.manual_status)] ?? 9;
        return sa - sb;
      });
  }, [parameters, filter, query]);

  const alertItems = parameters
    .filter((p) => p.maintenance?.maintenance_required)
    .sort((a, b) => (statusOrder[normalizeStatus(a.manual_status)] ?? 9) - (statusOrder[normalizeStatus(b.manual_status)] ?? 9))
    .slice(0, 4);

  const chartData = parameters
    .filter((p) => Number.isFinite(Number(p.analytics?.latest_value)) && Number.isFinite(Number(p.analytics?.historical?.mean)))
    .map((p) => ({
      name: (p.display_name || p.parameter).replace(/\(.*/, "").slice(0, 16),
      current: Number(p.analytics.latest_value),
      mean: Number(p.analytics.historical.mean)
    }));

  if (!result) {
    return (
      <UploadScreen
        aircraftId={aircraftId}
        setAircraftId={setAircraftId}
        file={file}
        setFile={setFile}
        onAnalyze={analyze}
        loading={loading}
        error={error}
      />
    );
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark small"><Plane size={19} /></div>
          <div>
            <strong>MAINTENANCE</strong>
            <span>INTELLIGENCE</span>
          </div>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">Workspace</span>
          <button type="button" className={`nav-item ${activeSection === "overview" ? "active" : ""}`} onClick={() => navigateTo("overview")}>
            <CircleGauge size={17} /> Overview
          </button>
          <button type="button" className={`nav-item ${activeSection === "live" ? "active" : ""}`} onClick={() => navigateTo("live")}>
            <Activity size={17} /> Live parameters
          </button>
          <button type="button" className={`nav-item ${activeSection === "maintenance" ? "active" : ""}`} onClick={() => navigateTo("maintenance")}>
            <Wrench size={17} /> Maintenance
            {counts.maintenance > 0 && <span className="nav-count">{counts.maintenance}</span>}
          </button>
          <button type="button" className={`nav-item ${activeSection === "evidence" ? "active" : ""}`} onClick={() => navigateTo("evidence")}>
            <BookOpen size={17} /> Manual evidence
          </button>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-label">Aircraft</span>
          <div className="aircraft-mini active">
            <span className="aircraft-dot" />
            <div><strong>{aircraft.aircraft_id || aircraftId}</strong><small>Current analysis</small></div>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="pipeline-status"><span className="live-dot" /> Pipeline online</div>
          <button className="secondary-button" onClick={() => { setResult(null); setError(""); }}>
            <Upload size={15} /> New analysis
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="mobile-menu icon-button" onClick={() => setSidebarOpen(!sidebarOpen)}><Menu size={19} /></button>
          <div>
            <span className="eyebrow">FLIGHT OPERATIONS / MAINTENANCE CONTROL</span>
            <h1>Aircraft health overview</h1>
          </div>
          <div className="topbar-actions">
            <div className="analysis-chip"><span className="live-dot" /> Analysis complete</div>
            <button className="icon-button"><Bell size={18} /></button>
            <button className="avatar">AM</button>
          </div>
        </header>

        <div className="content">
          <section id="overview-section" className="aircraft-banner">
            <div className="aircraft-title">
              <div className="plane-badge"><Plane size={22} /></div>
              <div>
                <span className="eyebrow">AIRCRAFT</span>
                <h2>{aircraft.aircraft_id || aircraftId}</h2>
                <p>Maintenance intelligence report · Pipeline v{result.pipeline_version || "1.1.0"}</p>
              </div>
            </div>
            <div className="banner-status">
              <span>OVERALL STATUS</span>
              <StatusBadge status={aircraft.overall_status} />
            </div>
          </section>

          <section className="metric-grid">
            <MetricCard icon={ShieldAlert} label="Risk score" value={`${formatNumber(aircraft.risk_score, 1)}%`} sub="Overall aircraft risk" tone="red" />
            <MetricCard icon={Clock3} label="Remaining useful life" value={formatNumber(aircraft.remaining_useful_life, 0)} sub="Cycles remaining" tone="amber" />
            <MetricCard icon={AlertTriangle} label="Anomalies detected" value={`${aircraft.anomalies_detected} / ${aircraft.parameters_analyzed}`} sub="Parameters outside statistical baseline" tone="orange" />
            <MetricCard icon={Wrench} label="Maintenance required" value={aircraft.maintenance_required_count} sub="Parameters requiring action" tone="violet" />
          </section>

          <section className="overview-grid">
            <div className="panel risk-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">AIRCRAFT RISK</span>
                  <h3>Operational risk profile</h3>
                </div>
                <span className="subtle-tag">Current flight data</span>
              </div>
              <div className="risk-layout">
                <RiskRing risk={aircraft.risk_score} />
                <div className="risk-copy">
                  <div className="risk-level"><span className="risk-dot" /> Elevated maintenance exposure</div>
                  <p>
                    {aircraft.anomalies_detected || 0} of {aircraft.parameters_analyzed || parameters.length}
                    {" "}monitored parameters show abnormal behavior. Prioritize critical manual conditions first.
                  </p>
                  <div className="risk-bars">
                    <div><span><b>Critical</b><b>{counts.CRITICAL}</b></span><i><em style={{ width: `${(counts.CRITICAL / Math.max(parameters.length, 1)) * 100}%` }} /></i></div>
                    <div><span><b>Warning</b><b>{counts.WARNING}</b></span><i><em style={{ width: `${(counts.WARNING / Math.max(parameters.length, 1)) * 100}%` }} /></i></div>
                    <div><span><b>Normal</b><b>{counts.NORMAL}</b></span><i><em style={{ width: `${(counts.NORMAL / Math.max(parameters.length, 1)) * 100}%` }} /></i></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">STATISTICAL VIEW</span>
                  <h3>Current vs historical mean</h3>
                </div>
                <BarChart3 size={18} className="muted-icon" />
              </div>
              <div className="chart-wrap">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 8, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="currentFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#7dd3fc" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#7dd3fc" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#233044" vertical={false} />
                    <XAxis dataKey="name" tick={{ fill: "#7f8da3", fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "#7f8da3", fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#0d1726", border: "1px solid #26354b", borderRadius: 10, color: "#eaf2ff" }} />
                    <Area type="monotone" dataKey="mean" name="Historical mean" stroke="#718096" fill="transparent" strokeDasharray="5 5" />
                    <Area type="monotone" dataKey="current" name="Current" stroke="#7dd3fc" fill="url(#currentFill)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section id="maintenance-section" className="section-block">
            <div className="section-header">
              <div>
                <span className="eyebrow">ACTION CENTER</span>
                <h3>Priority maintenance alerts</h3>
              </div>
              <span className="count-label">{aircraft.maintenance_required_count || alertItems.length} actions</span>
            </div>

            <div className="alert-grid">
              {alertItems.map((item) => (
                <button className="alert-card" key={item.parameter} onClick={() => setSelected(item)}>
                  <div className="alert-accent" />
                  <div className="alert-card-main">
                    <div className="alert-card-top">
                      <span className="alert-type"><ShieldAlert size={14} /> {item.maintenance?.priority || item.manual_status}</span>
                      <ChevronRight size={16} />
                    </div>
                    <h4>{item.display_name || item.parameter}</h4>
                    <div className="alert-value">
                      <strong>{formatNumber(item.analytics?.latest_value, 1)}</strong>
                      <span>{item.unit || ""}</span>
                    </div>
                    <p>{item.maintenance?.recommended_action || "Review parameter and maintenance evidence."}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section id="parameters-section" className="section-block">
            <div className="section-header">
              <div>
                <span className="eyebrow">PARAMETER MONITORING</span>
                <h3>All monitored parameters</h3>
              </div>
              <div className="controls">
                <div className="search-box">
                  <Search size={16} />
                  <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search parameters..." />
                </div>
                <div className="filter-group">
                  {["ALL", "CRITICAL", "WARNING", "NORMAL"].map((f) => (
                    <button key={f} className={filter === f ? "selected" : ""} onClick={() => setFilter(f)}>
                      {f === "ALL" ? "All" : f[0] + f.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="parameter-grid">
              {filtered.map((item) => (
                <ParameterCard key={item.parameter} item={item} onOpen={setSelected} />
              ))}
              {filtered.length === 0 && (
                <div className="empty-state">
                  <Search size={22} />
                  <strong>No parameters found</strong>
                  <span>Try another search or filter.</span>
                </div>
              )}
            </div>
          </section>

          <section id="evidence-section" className="section-block evidence-section">
            <div className="section-header">
              <div>
                <span className="eyebrow">SOURCE TRACEABILITY</span>
                <h3>Manual evidence</h3>
              </div>
              <span className="count-label">{parameters.filter(p => p.manual_evidence_available).length} sources available</span>
            </div>
            <div className="evidence-grid">
              {parameters.filter(p => p.manual_evidence_available).map((item) => (
                <button type="button" className="evidence-panel" key={item.parameter} onClick={() => setSelected(item)}>
                  <div className="evidence-panel-icon"><BookOpen size={17} /></div>
                  <div className="evidence-panel-copy">
                    <strong>{item.display_name || item.parameter}</strong>
                    <span>{item.manual_status || "UNKNOWN"} · {item.maintenance?.confidence || "—"} confidence</span>
                    <p>{item.maintenance?.recommended_action || "Manual evidence available for this parameter."}</p>
                  </div>
                  <ChevronRight size={16} />
                </button>
              ))}
              {parameters.filter(p => p.manual_evidence_available).length === 0 && (
                <div className="empty-state"><BookOpen size={22} /><strong>No manual evidence available</strong><span>The API did not return manual evidence for this analysis.</span></div>
              )}
            </div>
          </section>
        </div>
      </main>

      <DetailDrawer item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

export default App;
