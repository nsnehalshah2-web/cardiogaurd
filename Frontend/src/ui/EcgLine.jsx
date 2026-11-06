// Animated heartbeat trace. Decorative, so hidden from screen readers.
export default function EcgLine({ className = '', beats = 3 }) {
  const beat = 'l 18 0 l 6 -10 l 6 10 l 8 0 l 5 -46 l 7 72 l 6 -34 l 6 8 l 18 0';
  const path = `M 0 40 ${Array.from({ length: beats }, () => `${beat} l 40 0`).join(' ')}`;
  const width = beats * 120;
  return <svg className={`ecg-line ${className}`} viewBox={`0 0 ${width} 80`} preserveAspectRatio="none" aria-hidden="true" focusable="false">
    <path d={path} className="ecg-track" />
    <path d={path} className="ecg-trace" pathLength="1" />
  </svg>;
}
