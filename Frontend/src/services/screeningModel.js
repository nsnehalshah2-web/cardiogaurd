// Runs the home screening model in the browser, so screening works offline.
// Mirrors Backend/app/screening_model.py: same JSON parameters, same calculation.
import bundledModel from '../data/screening-model.json';
import { getScreeningModel } from './api';

const MODEL_KEY = 'cardioguard_screening_model';

export const defaultScreening = {
  age: 45, sex: 1, smoker: 0, cigs_per_day: 0, bp_medication: 0, prior_stroke: 0,
  hypertension: 0, diabetes: 0, systolic_bp: 125, bmi: null,
};

function cachedModel() {
  try { return JSON.parse(localStorage.getItem(MODEL_KEY)); } catch { return null; }
}

// Fetch the latest parameters when online; fall back to the copy saved on this device.
export async function loadScreeningModel() {
  try {
    const model = await getScreeningModel();
    try { localStorage.setItem(MODEL_KEY, JSON.stringify(model)); } catch { /* storage full or blocked */ }
    return model;
  } catch {
    // Offline: the last downloaded copy, else the copy built into the app.
    return cachedModel() || bundledModel;
  }
}

export function categoryFor(model, probability) {
  if (probability >= model.thresholds.high) return 'HIGH';
  if (probability >= model.thresholds.moderate) return 'MODERATE';
  return 'LOW';
}

export function predictScreening(model, input) {
  const values = { ...input, cigs_per_day: input.smoker ? input.cigs_per_day : 0 };
  const contributions = {};
  let logit = model.intercept;
  model.features.forEach((name, index) => {
    const raw = values[name];
    const value = raw === null || raw === undefined || raw === '' ? model.medians[index] : Number(raw);
    const contribution = model.coefficients[index] * (value - model.means[index]) / model.scales[index];
    contributions[name] = contribution;
    logit += contribution;
  });
  const probability = 1 / (1 + Math.exp(-logit));
  return {
    risk_probability: Math.round(probability * 10000) / 100,
    risk_category: categoryFor(model, probability),
    contributions,
  };
}

// Recommendation keys (translated in i18n.jsx). Mirrors recommendations() in the backend.
export function recommendationKeys(values, category) {
  const keys = [];
  if (category === 'HIGH') keys.push('rec.doctor');
  else if (category === 'MODERATE') keys.push('rec.checkup');
  if (values.smoker) keys.push('rec.smoking');
  if (values.systolic_bp >= 140) keys.push('rec.bpHigh');
  else if (values.systolic_bp >= 130) keys.push('rec.bpWatch');
  // Asian BMI cut-off for overweight is 23 (WHO expert consultation, 2004).
  if (values.bmi && values.bmi >= 23) keys.push('rec.weight');
  if (values.diabetes) keys.push('rec.sugar');
  if (!keys.length) keys.push('rec.keep');
  return keys.slice(0, 4);
}

// Factors pushing risk above average, largest first.
export function topFactors(contributions, limit = 3) {
  return Object.entries(contributions)
    .filter(([name, value]) => value > 0.05 && name !== 'smoker')
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name]) => name);
}

export function bmiFrom(heightCm, weightKg) {
  const h = Number(heightCm) / 100;
  const w = Number(weightKg);
  if (!h || !w) return null;
  return Math.round((w / (h * h)) * 10) / 10;
}
