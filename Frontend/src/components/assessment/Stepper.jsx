export default function Stepper({ current }) {
  const steps = ['Personal', 'Clinical', 'Lifestyle', 'Review'];
  return <div className="stepper">{steps.map((step, index) => <div className={`step ${index + 1 <= current ? 'done' : ''} ${index + 1 === current ? 'current' : ''}`} key={step}><span>{index + 1 < current ? '✓' : index + 1}</span><small>{step}</small></div>)}</div>;
}