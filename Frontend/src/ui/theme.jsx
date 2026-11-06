import { useEffect, useState } from 'react';
import { Monitor, Moon, Sun } from 'lucide-react';

const THEME_KEY = 'cardioguard_theme';
const ORDER = ['light', 'dark', 'system'];

export function storedTheme() {
  try { return localStorage.getItem(THEME_KEY) || 'system'; } catch { return 'system'; }
}

function systemPrefersDark() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches;
}

// index.html runs the same logic before React loads, so the page never flashes the wrong theme.
export function applyTheme(choice) {
  const resolved = choice === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : choice;
  document.documentElement.dataset.theme = resolved;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', resolved === 'dark' ? '#0a1417' : '#16776f');
}

export function setTheme(choice) {
  try { localStorage.setItem(THEME_KEY, choice); } catch { /* storage blocked */ }
  applyTheme(choice);
  window.dispatchEvent(new CustomEvent('cardioguard:theme', { detail: choice }));
}

export function useTheme() {
  const [theme, setThemeState] = useState(storedTheme);
  useEffect(() => {
    const onChange = (event) => setThemeState(event.detail);
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const onSystem = () => { if (storedTheme() === 'system') applyTheme('system'); };
    window.addEventListener('cardioguard:theme', onChange);
    media?.addEventListener('change', onSystem);
    return () => { window.removeEventListener('cardioguard:theme', onChange); media?.removeEventListener('change', onSystem); };
  }, []);
  return [theme, setTheme];
}

const ICONS = { light: Sun, dark: Moon, system: Monitor };
const LABELS = { light: 'Light theme', dark: 'Dark theme', system: 'System theme' };

export function ThemeToggle({ className = '' }) {
  const [theme, set] = useTheme();
  const Icon = ICONS[theme];
  const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
  return <button type="button" className={`icon-btn theme-toggle ${className}`} onClick={() => set(next)} aria-label={`${LABELS[theme]}. Switch to ${LABELS[next].toLowerCase()}`} title={LABELS[theme]}>
    <Icon size={18} key={theme} className="theme-icon" />
  </button>;
}
