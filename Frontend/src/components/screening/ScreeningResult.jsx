import { CircleAlert, Info, ListChecks, TrendingUp } from 'lucide-react';
import { useT } from '../../i18n';
import { recommendationKeys, topFactors } from '../../services/screeningModel';
import SpecialistPrompt from '../specialists/SpecialistPrompt';

export default function ScreeningResult({ result, values, offline, actions, showSpecialist = false }) {
  const { t } = useT();
  const factors = topFactors(result.contributions);
  const tone = result.risk_category.toLowerCase();
  const outOf100 = Math.max(1, Math.round(result.risk_probability));
  return <section className="panel screening-result">
    {offline && <div className="offline-note"><CircleAlert size={16} /> {t('screen.offlineNote')}</div>}
    <div className="screening-score">
      <div className={`score-ring ${tone}`} style={{ '--risk': `${Math.min(result.risk_probability * 2, 100)}%` }}>
        <strong>{result.risk_probability.toFixed(1)}<small>%</small></strong>
      </div>
      <div>
        <span className="eyebrow">{t('screen.resultTitle')}</span>
        <h2 className={`risk-text ${tone}`}>{t(`risk.${result.risk_category}`)}</h2>
        <p>{t('screen.resultOf100', { n: outOf100 })}</p>
        <PeopleGrid count={outOf100} tone={tone} />
      </div>
    </div>
    <div className="screening-columns">
      <div>
        <h3><TrendingUp size={16} /> {t('screen.topFactors')}</h3>
        {factors.length ? <ul className="factor-list">{factors.map((name) => <li key={name}>{t(`factor.${name}`)}</li>)}</ul> : <p className="muted-text">{t('screen.noFactors')}</p>}
      </div>
      <div>
        <h3><ListChecks size={16} /> {t('screen.nextSteps')}</h3>
        <ul className="rec-list">{recommendationKeys(values, result.risk_category).map((key) => <li key={key}><strong>{t(`${key}.title`)}</strong><span>{t(`${key}.detail`)}</span></li>)}</ul>
      </div>
    </div>
    {showSpecialist && <SpecialistPrompt band={result.risk_category} kind="home" />}
    <p className="model-footnote"><Info size={13} /> {t('screen.disclaimer')}</p>
    {actions && <div className="form-actions">{actions}</div>}
  </section>;
}

// 100 dots, with the affected ones coloured: easier to grasp than a percentage.
function PeopleGrid({ count, tone }) {
  return <div className="people-grid" aria-hidden="true">
    {Array.from({ length: 100 }, (_, index) => <i key={index} className={index < count ? `on ${tone}` : ''} />)}
  </div>;
}
