import { useEffect, useState } from 'react';
import { Bell, LockKeyhole, SlidersHorizontal } from 'lucide-react';
import { getReminderPreferences, updateReminderPreferences } from '../services/api';

export default function Settings() {
  const [preferences, setPreferences] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getReminderPreferences()
      .then(setPreferences)
      .catch(() => setError('We couldn’t load your reminder settings. Please refresh and try again.'));
  }, []);

  async function toggleReminders(event) {
    const email_enabled = event.target.checked;
    setSaving(true);
    setError('');
    try {
      setPreferences(await updateReminderPreferences({ email_enabled }));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'We couldn’t save this preference. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return <div className="settings-page">
    <div className="page-heading"><div><span className="eyebrow">Workspace preferences</span><h1>Settings</h1><p>Keep your CardioGuard experience focused and private.</p></div></div>
    <section className="panel settings-list">
      <div className="setting-row reminder-setting">
        <span className="setting-icon"><Bell size={18} /></span>
        <div className="reminder-setting-copy">
          <strong>Email follow-up reminders</strong>
          <p>Optional email reminders for screenings or referral follow-ups, sent to your account email. Emails contain no measurement values or notes. Turn this off any time.</p>
          {preferences && !preferences.email_configured && <p className="inline-notice">Email delivery is not configured yet, so reminders cannot be enabled.</p>}
          {error && <p className="inline-error" role="alert">{error}</p>}
        </div>
        <label className="switch-control">
          <span className="sr-only">Enable email follow-up reminders</span>
          <input
            type="checkbox"
            checked={preferences?.email_enabled ?? false}
            onChange={toggleReminders}
            disabled={!preferences || saving || (!preferences.email_configured && !preferences.email_enabled)}
          />
          <span>{saving ? 'Saving…' : preferences?.email_enabled ? 'On' : 'Off'}</span>
        </label>
      </div>
      <Setting icon={LockKeyhole} title="Security" text="Your session uses a signed JWT and expires automatically" />
      <Setting icon={SlidersHorizontal} title="Assessment preferences" text="Default clinical inputs are used only as a starting point" />
    </section>
  </div>;
}

function Setting({ icon: Icon, title, text }) {
  return <div className="setting-row"><span className="setting-icon"><Icon size={18} /></span><div><strong>{title}</strong><p>{text}</p></div><span className="setting-status">Active</span></div>;
}
