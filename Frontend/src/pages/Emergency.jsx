import { useState } from 'react';
import { ArrowRight, CircleCheck, HeartPulse } from 'lucide-react';
import { Link } from 'react-router-dom';
import EmergencyCheck from '../components/emergency/EmergencyCheck';
import { LanguageToggle, useT } from '../i18n';

// Public page: anyone can check warning signs without an account.
export default function Emergency() {
  const { t } = useT();
  const [clear, setClear] = useState(false);
  return <div className="public-page">
    <header className="landing-nav">
      <Link to="/" className="brand-mark"><span className="brand-icon"><HeartPulse size={19} /></span><span className="brand-copy"><strong>Cardio<span>Guard</span></strong><small>AI health intelligence</small></span></Link>
      <LanguageToggle />
    </header>
    <main className="public-main">
      {clear
        ? <section className="panel emergency-check">
          <span className="eyebrow"><CircleCheck size={13} /> {t('emergency.clearTitle')}</span>
          <h2>{t('emergency.clearTitle')}</h2>
          <p className="muted-text">{t('emergency.clearText')}</p>
          <div className="form-actions"><Link className="btn btn-primary" to="/home-screening">{t('emergency.toScreening')} <ArrowRight size={17} /></Link></div>
        </section>
        : <EmergencyCheck onClear={() => setClear(true)} />}
    </main>
  </div>;
}
