import { CheckCircle2, ClipboardCheck } from 'lucide-react';

export default function ActionPlan({ items = [] }) {
  return (
    <section className="panel action-plan-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow"><ClipboardCheck size={13} /> Personalized guidance</span>
          <h2>Your action plan</h2>
        </div>
      </div>
      {items.length ? (
        <div className="action-plan-list">
          {items.map((item, index) => (
            <div className="action-plan-item" key={`${item.title}-${index}`}>
              <span className="action-plan-number">{index + 1}</span>
              <div>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>
              <CheckCircle2 size={17} />
            </div>
          ))}
        </div>
      ) : (
        <p className="action-plan-empty">No priority flags were identified from the values in this assessment.</p>
      )}
      <p className="action-plan-disclaimer">This is general educational guidance, not a diagnosis or treatment plan.</p>
    </section>
  );
}
