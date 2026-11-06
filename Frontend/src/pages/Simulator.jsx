import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  RefreshCcw,
  SlidersHorizontal,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";
import { submitAssessment } from "../services/api";
import { defaultHealthData } from "../services/storage";
import useHistoryData from "../hooks/useHistoryData";

export default function Simulator() {
  const { history, loading: historyLoading } = useHistoryData();
  const latest = history[0];
  // Assessments saved before chest pain type was added have cp = null.
  const baselineData = useMemo(
    () =>
      latest?.form_data
        ? { ...latest.form_data, cp: latest.form_data.cp ?? defaultHealthData.cp }
        : defaultHealthData,
    [latest?.form_data],
  );
  const [simData, setSimData] = useState(baselineData);
  const [baselineRisk, setBaselineRisk] = useState(null);
  const [simRisk, setSimRisk] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setSimData(baselineData);
    setBaselineRisk(null);
    setSimRisk(null);
  }, [latest?.id]);
  useEffect(() => {
    if (historyLoading) return;
    let active = true;
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const [baselineResult, scenarioResult] = await Promise.all([
          submitAssessment(baselineData, false),
          submitAssessment(simData, false),
        ]);
        if (active) {
          setBaselineRisk(baselineResult.risk_probability);
          setSimRisk(scenarioResult.risk_probability);
          setError("");
        }
      } catch {
        if (active)
          setError(
            "Live simulation is unavailable. Check the backend connection.",
          );
      } finally {
        if (active) setLoading(false);
      }
    }, 450);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [baselineData, simData, historyLoading]);
  const change =
    baselineRisk === null || simRisk === null
      ? 0
      : Number(simRisk) - Number(baselineRisk);
  const changed = (key) => simData[key] !== baselineData[key];
  const update = (key, value) =>
    setSimData((data) => ({ ...data, [key]: Number(value) }));
  if (historyLoading)
    return (
      <div className="auth-loading">
        <div className="loading-spinner" />
        <span>Loading your private baseline...</span>
      </div>
    );
  return (
    <div className="simulator-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Interactive exploration</span>
          <h1>What-if lab</h1>
          <p>
            Adjust one signal at a time and see how the model responds to a
            different scenario.
          </p>
        </div>
        <button
          className="btn btn-ghost"
          onClick={() => setSimData(baselineData)}
        >
          <RefreshCcw size={16} /> Reset to baseline
        </button>
      </div>
      <div className="simulator-grid">
        <section className="panel controls-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">
                <SlidersHorizontal size={13} /> Scenario controls
              </span>
              <h2>Shape a different picture</h2>
            </div>
            <span className="live-label">
              <i /> Live model
            </span>
          </div>
          <Slider
            label="Resting blood pressure"
            helper="Systolic · mmHg"
            value={simData.trestbps}
            baseline={baselineData.trestbps}
            min={90}
            max={200}
            unit="mmHg"
            onChange={(value) => update("trestbps", value)}
            changed={changed("trestbps")}
          />
          <Slider
            label="Total cholesterol"
            helper="mg/dL"
            value={simData.chol}
            baseline={baselineData.chol}
            min={100}
            max={400}
            unit="mg/dL"
            onChange={(value) => update("chol", value)}
            changed={changed("chol")}
          />
          <Slider
            label="Maximum heart rate"
            helper="BPM achieved"
            value={simData.thalach}
            baseline={baselineData.thalach}
            min={70}
            max={220}
            unit="BPM"
            onChange={(value) => update("thalach", value)}
            changed={changed("thalach")}
          />
          <div className="control-foot">
            <Activity size={16} />
            <span>
              Other health signals stay anchored to your latest assessment.
            </span>
          </div>
        </section>
        <section className="panel simulation-result">
          <div className="sim-result-top">
            <span className="eyebrow">Estimated scenario</span>
            {loading && (
              <span className="calculating">
                <i /> recalculating
              </span>
            )}
          </div>
          <div className="sim-numbers">
            <div>
              <small>Current</small>
              <strong>
                {baselineRisk !== null
                  ? `${Number(baselineRisk).toFixed(2)}%`
                  : "--"}
              </strong>
              <span>baseline risk</span>
            </div>
            <ArrowRight size={28} className="sim-arrow" />
            <div className="sim-current">
              <small>Simulated</small>
              <strong>
                {simRisk !== null ? `${Number(simRisk).toFixed(2)}%` : "--"}
              </strong>
              <span>new estimate</span>
            </div>
          </div>
          <div
            className={`change-banner ${change < 0 ? "down" : change > 0 ? "up" : ""}`}
          >
            {change < 0 ? (
              <TrendingDown size={18} />
            ) : change > 0 ? (
              <TrendingUp size={18} />
            ) : (
              <Activity size={18} />
            )}
            <strong>
              {change === 0
                ? "No change yet"
                : `${Math.abs(change).toFixed(0)} percentage points`}
            </strong>
            <span>
              {change < 0
                ? "lower than baseline"
                : change > 0
                  ? "higher than baseline"
                  : "Adjust a slider to compare"}
            </span>
          </div>
          <div className="scenario-note">
            <Sparkles size={17} />
            <p>
              This is a model scenario, not a forecast. Use it to identify
              useful questions for a qualified clinician.
            </p>
          </div>
          {error && <p className="form-error">{error}</p>}
          <Link className="subtle-link" to="/assessment">
            Update your full assessment <ArrowRight size={15} />
          </Link>
        </section>
      </div>
    </div>
  );
}
function Slider({
  label,
  helper,
  value,
  baseline,
  min,
  max,
  unit,
  onChange,
  changed,
}) {
  return (
    <div className={`slider-row ${changed ? "changed" : ""}`}>
      <div className="slider-label">
        <div>
          <strong>{label}</strong>
          <span>{helper}</span>
        </div>
        <strong className="slider-value">
          {value} <small>{unit}</small>
        </strong>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{ "--progress": `${((value - min) / (max - min)) * 100}%` }}
      />
      <div className="slider-meta">
        <span>{min}</span>
        <span>{changed ? `Baseline ${baseline}` : "Baseline"}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
