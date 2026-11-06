import { AnimatedValue } from '../../ui/CountUp';

export default function StatCard({ icon: Icon, label, value, meta, tone = 'blue' }) {
  return <div className="stat-card">
    <div className={`stat-icon ${tone}`}><Icon size={19} /></div>
    <div className="stat-copy"><span>{label}</span><strong><AnimatedValue value={value} /></strong><small>{meta}</small></div>
  </div>;
}
