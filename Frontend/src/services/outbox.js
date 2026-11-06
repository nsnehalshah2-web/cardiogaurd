// Community screening records are written here first, then sent to the server.
// If the phone is offline they wait here until the next sync, so nothing is lost.
import { getPatients, syncCommunity } from './api';

const key = (userId, name) => `cardioguard_${name}_${userId}`;

function read(userId, name, fallback) {
  try { return JSON.parse(localStorage.getItem(key(userId, name))) ?? fallback; } catch { return fallback; }
}

function write(userId, name, value) {
  localStorage.setItem(key(userId, name), JSON.stringify(value));
}

export const newClientId = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`).replace(/-/g, '');

export function getOutbox(userId) {
  return read(userId, 'outbox', { patients: [], screenings: [] });
}

export function pendingCount(userId) {
  const box = getOutbox(userId);
  return box.patients.length + box.screenings.length;
}

export function queuePatient(userId, patient) {
  const box = getOutbox(userId);
  box.patients = [...box.patients.filter((item) => item.client_id !== patient.client_id), patient];
  write(userId, 'outbox', box);
}

export function queueScreening(userId, screening) {
  const box = getOutbox(userId);
  box.screenings.push(screening);
  write(userId, 'outbox', box);
}

// Send everything waiting. The server ignores records it has already saved, so a retry is safe.
export async function flushOutbox(userId) {
  const box = getOutbox(userId);
  if (!box.patients.length && !box.screenings.length) return { sent: 0 };
  await syncCommunity({
    patients: box.patients.map(({ client_id, name, age, sex, village, phone }) => ({ client_id, name, age, sex, village, phone })),
    screenings: box.screenings.map(({ result, ...screening }) => screening),
  });
  // Keep anything queued while the request was in flight.
  const latest = getOutbox(userId);
  const sentPatients = new Set(box.patients.map((item) => item.client_id));
  const sentScreenings = new Set(box.screenings.map((item) => item.client_id));
  write(userId, 'outbox', {
    patients: latest.patients.filter((item) => !sentPatients.has(item.client_id)),
    screenings: latest.screenings.filter((item) => !sentScreenings.has(item.client_id)),
  });
  return { sent: sentPatients.size + sentScreenings.size };
}

// Server patient list, cached so the list still shows offline.
export async function loadPatients(userId) {
  try {
    const patients = await getPatients();
    write(userId, 'patients', patients);
    return { patients, offline: false };
  } catch {
    return { patients: read(userId, 'patients', []), offline: true };
  }
}
