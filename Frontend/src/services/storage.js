const KEY = 'cardioguard_assessments';

export const defaultHealthData = { age: 50, sex: 1, cp: 4, trestbps: 120, chol: 200, fbs: 0, restecg: 1, thalach: 150, exang: 0, oldpeak: 1.0 };

export function getAssessments() {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
}

export function saveAssessment(result, formData) {
  const entry = { id: Date.now(), createdAt: new Date().toISOString(), result, formData };
  const next = [entry, ...getAssessments()].slice(0, 12);
  localStorage.setItem(KEY, JSON.stringify(next));
  return entry;
}

export function getLatestAssessment() { return getAssessments()[0] || null; }