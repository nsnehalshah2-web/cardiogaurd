import { useMemo, useState } from 'react';
import { Activity, Cigarette, Droplets, Info } from 'lucide-react';
import model from '../../data/screening-model.json';
import { predictScreening, topFactors } from '../../services/screeningModel';
import CountUp from '../../ui/CountUp';

const FACTOR_LABELS = {
  age: 'Age', sex: 'Being male', cigs_per_day: 'Smoking', bp_medication: 'BP medicine', prior_stroke: 'Previous stroke',
  hypertension: 'High blood pressure', diabetes: 'Diabetes', systolic_bp: 'Blood pressure', bmi: 'Weight',
};
const BAND = { LOW: 'Low risk', MODERATE: 'Moderate risk', HIGH: 'High risk' };

// The real home screening model running in the browser: drag the sliders and the estimate updates live.
export default function LiveRiskDemo() {
  const [values, setValues] = useState({ age: 45, sex: 1, systolic_bp: 128, smoker: 0, diabetes: 0 });
  const set = (key, value) => setValues((current) => ({ ...current, [key]: value }));
  const result = useMemo(() => predictScreening(model, {
    ...values, cigs_per_day: values.smoker ? 15 : 0, hypertension: values.systolic_bp >= 140 ? 1 : 0,
    bp_medication: 0, prior_stroke: 0, bmi: null,
  }), [values]);
  const tone = result.risk_category.toLowerCase();
  const outOf100 = Math.max(1, Math.round(result.risk_probability));
  const factors = topFactors(result.contributions, 2);
  const circumference = 2 * Math.PI * 52;

  return <div className={`live-demo tone-${tone}`} data-tilt>
    <div className="live-demo-head">
      <span className="live-badge"><span className="live-dot" /> Live model</span>
      <small>Try it: drag the sliders</small>
    </div>
    <div className="live-demo-score">
      <div className="demo-ring" role="img" aria-label={`${result.risk_probability.toFixed(1)}% ten-year risk`}>
        <svg viewBox="0 0 120 120" aria-hidden="true">
          <circle cx="60" cy="60" r="52" className="ring-track" />
          <circle cx="60" cy="60" r="52" className="ring-value" strokeDasharray={circumference}
            style={{ strokeDashoffset: circumference * (1 - Math.min(result.risk_probability * 2, 100) / 100) }} />
        </svg>
        <strong><CountUp value={result.risk_probability} decimals={1} duration={450} /><small>%</small></strong>
      </div>
      <div>
        <span className="demo-label">10-year heart risk</span>
        <h3 className={`demo-band ${tone}`} aria-live="polite">{BAND[result.risk_category]}</h3>
        <p>{outOf100} in 100 people like this develop heart disease within 10 years.</p>
      </div>
    </div>
    <div className="demo-dots" aria-hidden="true">{Array.from({ length: 100 }, (_, index) => <i key={index} className={index < outOf100 ? 'on' : ''} />)}</div>

    <div className="demo-controls">
      <Slider label="Age" unit="years" min={32} max={70} value={values.age} onChange={(value) => set('age', value)} />
      <Slider label="Blood pressure (upper)" unit="mmHg" min={95} max={200} value={values.systolic_bp} onChange={(value) => set('systolic_bp', value)} />
      <div className="demo-toggles">
        <Toggle icon={Activity} label={values.sex ? 'Male' : 'Female'} active onClick={() => set('sex', values.sex ? 0 : 1)} ariaLabel={`Sex: ${values.sex ? 'male' : 'female'}. Tap to change`} />
        <Toggle icon={Cigarette} label="Smoker" active={values.smoker === 1} onClick={() => set('smoker', values.smoker ? 0 : 1)} />
        <Toggle icon={Droplets} label="Diabetes" active={values.diabetes === 1} onClick={() => set('diabetes', values.diabetes ? 0 : 1)} />
      </div>
    </div>
    <p className="demo-foot"><Info size={13} /> {factors.length ? `Biggest drivers: ${factors.map((name) => FACTOR_LABELS[name]).join(' and ')}.` : 'No single factor stands out.'} Framingham Heart Study model, not a diagnosis.</p>
  </div>;
}

function Slider({ label, unit, min, max, value, onChange }) {
  const fill = ((value - min) / (max - min)) * 100;
  return <label className="demo-slider">
    <span>{label}<strong>{value} <small>{unit}</small></strong></span>
    <input type="range" min={min} max={max} value={value} onChange={(event) => onChange(Number(event.target.value))} style={{ '--fill': `${fill}%` }} />
  </label>;
}

function Toggle({ icon: Icon, label, active, onClick, ariaLabel }) {
  return <button type="button" className={`demo-toggle ${active ? 'active' : ''}`} onClick={onClick} aria-pressed={ariaLabel ? undefined : active} aria-label={ariaLabel}>
    <Icon size={15} /> {label}
  </button>;
}
