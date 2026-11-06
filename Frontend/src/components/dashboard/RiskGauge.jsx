import { ShieldCheck } from 'lucide-react';
import CountUp from '../../ui/CountUp';

// Animated ring gauge: the arc sweeps to the risk value while the number counts up.
export default function RiskGauge({ value = 0, category = 'LOW' }) {
  const tone = category.toLowerCase();
  const risk = Math.min(Math.max(Number(value) || 0, 0), 100);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  return <div className="gauge-wrap">
    <div className={`risk-ring ${tone}`} role="img" aria-label={`${risk.toFixed(1)}% risk estimate, ${tone} risk`}>
      <svg viewBox="0 0 200 200" aria-hidden="true">
        <defs>
          <linearGradient id={`ring-${tone}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" className="ring-stop-a" />
            <stop offset="100%" className="ring-stop-b" />
          </linearGradient>
        </defs>
        <circle cx="100" cy="100" r={radius} className="ring-track" />
        <circle cx="100" cy="100" r={radius} className="ring-value" stroke={`url(#ring-${tone})`}
          strokeDasharray={circumference} style={{ '--ring-offset': circumference * (1 - risk / 100), '--ring-full': circumference }} />
      </svg>
      <div className="gauge-inner"><ShieldCheck size={22} /><strong><CountUp value={risk} decimals={1} /><small>%</small></strong><span>risk estimate</span></div>
    </div>
    <div className={`risk-pill ${tone}`}>{category} RISK</div>
  </div>;
}
