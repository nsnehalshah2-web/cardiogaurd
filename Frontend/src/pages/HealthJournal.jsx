import { useEffect, useMemo, useState } from 'react';
import { Activity, Bell, HeartPulse, Plus, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  addMeasurement, addReminder, deleteMeasurement, getMeasurements, getReminderPreferences,
  getReminders, updateReminder,
} from '../services/api';

const localInputTime = (date = new Date()) =>
  new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
const emptyMeasurement = () => ({
  measured_at: localInputTime(),
  systolic_bp: '',
  diastolic_bp: '',
  weight_kg: '',
  heart_rate: '',
  note: '',
});
const errorText = (error, fallback) => error.response?.data?.detail || fallback;

export default function HealthJournal() {
  const [measurements, setMeasurements] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [measurement, setMeasurement] = useState(emptyMeasurement);
  const [reminder, setReminder] = useState({
    kind: 'screening',
    scheduled_at: localInputTime(new Date(Date.now() + 7 * 86400000)),
    note: '',
  });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function loadJournal() {
    setError('');
    try {
      const [measurementRows, reminderRows, preferences] = await Promise.all([
        getMeasurements(), getReminders(), getReminderPreferences(),
      ]);
      setMeasurements(measurementRows);
      setReminders(reminderRows);
      setEmailEnabled(preferences.email_enabled);
    } catch (requestError) {
      setError(errorText(requestError, 'We couldn’t load your health journal. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadJournal(); }, []);

  async function submitMeasurement(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    const values = {
      measured_at: new Date(measurement.measured_at).toISOString(),
      note: measurement.note.trim() || null,
    };
    for (const key of ['systolic_bp', 'diastolic_bp', 'weight_kg', 'heart_rate']) {
      if (measurement[key] !== '') values[key] = Number(measurement[key]);
    }
    try {
      const created = await addMeasurement(values);
      setMeasurements((current) => [created, ...current].sort((a, b) => new Date(b.measured_at) - new Date(a.measured_at)));
      setMeasurement(emptyMeasurement());
      setNotice('Measurement saved to your private history.');
    } catch (requestError) {
      setError(errorText(requestError, 'We couldn’t save this measurement. Check the values and try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function removeMeasurement(id) {
    setBusy(true);
    setError('');
    try {
      await deleteMeasurement(id);
      setMeasurements((current) => current.filter((entry) => entry.id !== id));
      setNotice('Measurement removed.');
    } catch (requestError) {
      setError(errorText(requestError, 'We couldn’t remove this measurement. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function submitReminder(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const created = await addReminder({
        ...reminder,
        scheduled_at: new Date(reminder.scheduled_at).toISOString(),
        note: reminder.note.trim() || null,
      });
      setReminders((current) => [created, ...current].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at)));
      setNotice('Email reminder scheduled.');
      setReminder((current) => ({ ...current, note: '' }));
    } catch (requestError) {
      setError(errorText(requestError, 'We couldn’t schedule this reminder. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function cancelReminder(id) {
    setBusy(true);
    setError('');
    try {
      const updated = await updateReminder(id, { enabled: false });
      setReminders((current) => current.map((item) => item.id === id ? updated : item));
      setNotice('Reminder turned off.');
    } catch (requestError) {
      setError(errorText(requestError, 'We couldn’t update this reminder. Please try again.'));
    } finally {
      setBusy(false);
    }
  }

  const charts = useMemo(() => [
    { key: 'systolic_bp', label: 'Systolic blood pressure', unit: 'mmHg', color: '#2f9d8f' },
    { key: 'diastolic_bp', label: 'Diastolic blood pressure', unit: 'mmHg', color: '#6383c4' },
    { key: 'weight_kg', label: 'Weight', unit: 'kg', color: '#d48756' },
    { key: 'heart_rate', label: 'Heart rate', unit: 'bpm', color: '#bd6b82' },
  ].map((chart) => ({
    ...chart,
    metricKey: chart.key,
    points: [...measurements].reverse().filter((entry) => Number.isFinite(Number(entry[chart.key])) && entry[chart.key] != null),
  })).filter((chart) => chart.points.length), [measurements]);

  if (loading) return <div className="auth-loading"><div className="loading-spinner" /><span>Loading your health journal…</span></div>;

  return <div className="health-journal-page">
    <div className="page-heading">
      <div><span className="eyebrow">Your personal health history</span><h1>Measurements & reminders</h1><p>Keep dated measurements and optional follow-up reminders together.</p></div>
    </div>
    {error && <div className="journal-feedback error" role="alert">{error}<button type="button" className="subtle-link" onClick={loadJournal}>Retry</button></div>}
    {notice && <div className="journal-feedback success" role="status">{notice}</div>}

    <section className="journal-section">
      <div className="journal-section-heading"><div><span className="eyebrow">Track over time</span><h2>Health measurements</h2><p>Measurements are shown separately from CardioGuard risk estimates.</p></div></div>
      <div className="journal-trend-grid">
        {charts.length ? charts.map(({ key, ...chart }) => <TrendChart key={key} {...chart} />) : <div className="panel journal-empty">Add measurements to see personal trends here.</div>}
      </div>
      <div className="journal-disclaimer">Trends are for your records only. They are not a diagnosis or a CardioGuard risk estimate. Discuss concerning readings with a qualified healthcare professional.</div>

      <div className="journal-columns">
        <form className="panel journal-form" onSubmit={submitMeasurement}>
          <div className="panel-heading"><div><span className="eyebrow"><HeartPulse size={14} /> New entry</span><h2>Record a measurement</h2></div></div>
          <label>Date and time (local)<input required type="datetime-local" value={measurement.measured_at} onChange={(event) => setMeasurement({ ...measurement, measured_at: event.target.value })} /></label>
          <div className="journal-input-grid">
            <label>Systolic BP (mmHg)<input type="number" min="50" max="300" value={measurement.systolic_bp} onChange={(event) => setMeasurement({ ...measurement, systolic_bp: event.target.value })} placeholder="e.g. 120" /></label>
            <label>Diastolic BP (mmHg)<input type="number" min="30" max="200" value={measurement.diastolic_bp} onChange={(event) => setMeasurement({ ...measurement, diastolic_bp: event.target.value })} placeholder="e.g. 80" /></label>
            <label>Weight (kg)<input type="number" min="1" max="500" step="0.1" value={measurement.weight_kg} onChange={(event) => setMeasurement({ ...measurement, weight_kg: event.target.value })} placeholder="Optional" /></label>
            <label>Heart rate (bpm)<input type="number" min="20" max="250" value={measurement.heart_rate} onChange={(event) => setMeasurement({ ...measurement, heart_rate: event.target.value })} placeholder="Optional" /></label>
          </div>
          <label>Note (optional)<textarea maxLength="300" rows="2" value={measurement.note} onChange={(event) => setMeasurement({ ...measurement, note: event.target.value })} placeholder="Context for your own records" /></label>
          <button className="btn btn-primary" type="submit" disabled={busy}><Plus size={16} /> Save measurement</button>
        </form>

        <section className="panel journal-history">
          <div className="panel-heading"><div><span className="eyebrow"><Activity size={14} /> Your entries</span><h2>Recent measurements</h2></div></div>
          {measurements.length === 0 ? <p className="journal-empty-copy">No measurements recorded yet.</p> : <div className="measurement-list">
            {measurements.map((entry) => <article className="measurement-entry" key={entry.id}>
              <div><strong>{new Date(entry.measured_at).toLocaleString()}</strong><p>{measurementSummary(entry)}</p>{entry.note && <small>{entry.note}</small>}</div>
              <button className="icon-btn" type="button" disabled={busy} onClick={() => removeMeasurement(entry.id)} aria-label="Delete measurement"><Trash2 size={16} /></button>
            </article>)}
          </div>}
        </section>
      </div>
    </section>

    <section className="journal-section reminder-section">
      <div className="journal-section-heading"><div><span className="eyebrow"><Bell size={14} /> Optional email</span><h2>Follow-up reminders</h2><p>One-time reminders for a repeat screening or referral follow-up.</p></div></div>
      {!emailEnabled ? <div className="panel reminder-optin">
        <p>Email reminders are off. Opt in from Settings before scheduling; you can turn them off at any time.</p>
        <Link className="btn btn-ghost" to="/settings">Open reminder settings</Link>
      </div> : <form className="panel reminder-form" onSubmit={submitReminder}>
        <label>Reminder type<select value={reminder.kind} onChange={(event) => setReminder({ ...reminder, kind: event.target.value })}><option value="screening">Repeat a screening</option><option value="referral">Follow up on a referral</option></select></label>
        <label>Date and time (local)<input required type="datetime-local" value={reminder.scheduled_at} onChange={(event) => setReminder({ ...reminder, scheduled_at: event.target.value })} /></label>
        <label>Note for your account (not included in email)<input maxLength="240" value={reminder.note} onChange={(event) => setReminder({ ...reminder, note: event.target.value })} placeholder="Optional" /></label>
        <button className="btn btn-primary" type="submit" disabled={busy}><Plus size={16} /> Schedule reminder</button>
      </form>}
      <div className="panel reminder-list">
        <h3>Scheduled reminders</h3>
        {reminders.length === 0 ? <p className="journal-empty-copy">No reminders scheduled.</p> : reminders.map((item) => <article className="reminder-entry" key={item.id}>
          <div><strong>{item.kind === 'screening' ? 'Repeat a screening' : 'Follow up on a referral'}</strong><p>{new Date(item.scheduled_at).toLocaleString()}</p>{item.note && <small>{item.note}</small>}<span className={`reminder-status ${item.sent_at ? 'sent' : item.enabled ? 'pending' : 'off'}`}>{item.sent_at ? 'Sent' : item.enabled ? 'Scheduled' : 'Off'}</span></div>
          {item.enabled && <button className="btn btn-ghost" type="button" disabled={busy} onClick={() => cancelReminder(item.id)}>Turn off</button>}
        </article>)}
      </div>
      <p className="reminder-delivery-note">Delivery is by email and may be delayed while the service starts from idle. Emails contain only a generic reminder, not your measurements or notes.</p>
    </section>
  </div>;
}

function measurementSummary(entry) {
  return [
    entry.systolic_bp != null && `BP ${entry.systolic_bp}/${entry.diastolic_bp} mmHg`,
    entry.weight_kg != null && `${entry.weight_kg} kg`,
    entry.heart_rate != null && `${entry.heart_rate} bpm`,
  ].filter(Boolean).join(' · ');
}

function TrendChart({ label, unit, points, color, metricKey }) {
  const values = points.map((point) => Number(point[metricKey]));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const coordinates = values.map((value, index) => {
    const x = values.length === 1 ? 50 : 8 + (index / (values.length - 1)) * 84;
    const y = 52 - ((value - min) / spread) * 40;
    return { x, y, value, entry: points[index] };
  });
  return <article className="panel trend-card">
    <div className="trend-card-heading"><div><span>{label}</span><strong>{values.at(-1)} {unit}</strong></div><span>{points.length} {points.length === 1 ? 'entry' : 'entries'}</span></div>
    <svg viewBox="0 0 100 60" role="img" aria-label={`${label} personal trend`}>
      <line x1="5" x2="95" y1="53" y2="53" stroke="#dce8e5" strokeWidth="1" />
      {coordinates.length > 1 && <polyline points={coordinates.map(({ x, y }) => `${x},${y}`).join(' ')} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />}
      {coordinates.map(({ x, y, value, entry }) => <circle key={`${entry.id}-${value}`} cx={x} cy={y} r="2.4" fill={color}><title>{value} {unit}, {new Date(entry.measured_at).toLocaleDateString()}</title></circle>)}
    </svg>
    <small>Most recent: {new Date(points.at(-1).measured_at).toLocaleDateString()}</small>
  </article>;
}
