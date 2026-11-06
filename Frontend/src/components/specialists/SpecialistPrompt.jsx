import { ArrowRight, FileText, Stethoscope } from 'lucide-react';
import { Link } from 'react-router-dom';

// Shown after a result. Suggests a relevant specialty without implying a diagnosis.
export default function SpecialistPrompt({ band, kind = 'clinical' }) {
  return <section className="specialist-prompt">
    <span className="specialist-prompt-icon" aria-hidden="true"><Stethoscope size={22} /></span>
    <div className="specialist-prompt-copy">
      <h3>Want to discuss your results with a professional?</h3>
      <p>Consider discussing your assessment with a qualified healthcare professional. For heart-related risk, a <strong>cardiologist</strong> is a good place to start.</p>
    </div>
    <div className="specialist-prompt-actions">
      <Link className="btn btn-primary" to="/specialists" state={{ risk: true, band, kind }}>Find a specialist near me <ArrowRight size={16} /></Link>
      <Link className="btn btn-ghost" to="/reports"><FileText size={16} /> Share assessment with doctor</Link>
    </div>
  </section>;
}
