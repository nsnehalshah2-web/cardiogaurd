import { useEffect, useState } from 'react';
import { Download, RotateCcw } from 'lucide-react';
import EmergencyCheck from '../components/emergency/EmergencyCheck';
import ScreeningForm from '../components/screening/ScreeningForm';
import ScreeningResult from '../components/screening/ScreeningResult';
import { useAuth } from '../context/AuthContext';
import { useT } from '../i18n';
import { getScreeningHistory, submitScreening } from '../services/api';
import { downloadDoctorReport } from '../services/pdfReport';
import { loadScreeningModel, predictScreening } from '../services/screeningModel';

export default function HomeScreening() {
  const { t } = useT();
  const { user } = useAuth();
  const [stage, setStage] = useState('emergency');
  const [values, setValues] = useState(null);
  const [result, setResult] = useState(null);
  const [offline, setOffline] = useState(false);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');

  const refreshHistory = () => getScreeningHistory().then(setHistory).catch(() => {});
  useEffect(() => { refreshHistory(); loadScreeningModel().catch(() => {}); }, []);

  const submit = async (data) => {
    setValues(data);
    setError('');
    try {
      const response = await submitScreening(data);
      setResult(response);
      setOffline(false);
      refreshHistory();
    } catch (error) {
      if (error.response) { setError(error.response.data?.detail?.[0]?.msg || error.response.data?.detail || 'Something went wrong.'); return; }
      // No connection: calculate on this device with the saved model.
      try {
        setResult(predictScreening(await loadScreeningModel(), data));
        setOffline(true);
      } catch {
        setError(t('community.offlineDetail'));
        return;
      }
    }
    setStage('result');
  };

  const latestSaved = history[0];
  return <div className="screening-page">
    <div className="page-heading compact-heading"><div><span className="eyebrow">{t('screen.eyebrow')}</span><h1>{t('screen.title')}</h1><p>{t('screen.text')}</p></div></div>
    {stage === 'emergency' && <EmergencyCheck onClear={() => setStage('form')} />}
    {stage === 'form' && <section className="panel">{error && <div className="form-error">{String(error)}</div>}<ScreeningForm initial={values} onSubmit={submit} /></section>}
    {stage === 'result' && result && <ScreeningResult result={result} values={values} offline={offline} showSpecialist actions={<>
      <button type="button" className="btn btn-ghost" onClick={() => setStage('form')}><RotateCcw size={16} /> {t('screen.again')}</button>
      {!offline && latestSaved && <button type="button" className="btn btn-primary" onClick={() => downloadDoctorReport({ userName: user?.name, screening: latestSaved })}><Download size={16} /> {t('screen.report')}</button>}
    </>} />}
    {history.length > 0 && <section className="panel screening-history">
      <h3>{t('screen.history')}</h3>
      <ul>{history.slice(0, 8).map((item) => <li key={item.id}>
        <span>{new Date(item.screened_at).toLocaleDateString()}</span>
        <strong className={`risk-text ${item.risk_category.toLowerCase()}`}>{item.risk_probability.toFixed(1)}%</strong>
        <span className={`risk-chip ${item.risk_category.toLowerCase()}`}>{t(`risk.${item.risk_category}`)}</span>
      </li>)}</ul>
    </section>}
  </div>;
}
