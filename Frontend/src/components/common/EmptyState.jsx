import { ArrowRight, ClipboardList } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function EmptyState({ title = 'Your health journey starts here', text = 'Complete your first assessment to unlock your personal cardiovascular baseline.', action = 'Start assessment' }) {
  return <div className="empty-state">
    <div className="empty-icon"><ClipboardList size={28} /></div><h2>{title}</h2><p>{text}</p>
    <Link className="btn btn-primary" to="/assessment">{action}<ArrowRight size={17} /></Link>
  </div>;
}