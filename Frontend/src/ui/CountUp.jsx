import { useEffect, useRef, useState } from 'react';

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
const easeOutCubic = (t) => 1 - (1 - t) ** 3;

// Animates a number from its previous value to the new one. With startOnView it waits
// until the element scrolls into view. Screen readers get the final value immediately.
export default function CountUp({ value, decimals = 0, duration = 900, prefix = '', suffix = '', startOnView = false, className }) {
  const target = Number(value) || 0;
  const [shown, setShown] = useState(prefersReducedMotion() ? target : 0);
  const from = useRef(0);
  const ref = useRef(null);
  const [visible, setVisible] = useState(!startOnView);

  useEffect(() => {
    if (!startOnView || !ref.current) return undefined;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); observer.disconnect(); }
    }, { threshold: 0.4 });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [startOnView]);

  useEffect(() => {
    if (!visible) return undefined;
    if (prefersReducedMotion()) { setShown(target); from.current = target; return undefined; }
    const start = performance.now();
    const origin = from.current;
    let frame;
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      setShown(origin + (target - origin) * easeOutCubic(progress));
      if (progress < 1) frame = requestAnimationFrame(tick);
      else from.current = target;
    };
    frame = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(frame); from.current = target; };
  }, [target, duration, visible]);

  const text = `${prefix}${shown.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
  const final = `${prefix}${target.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${suffix}`;
  return <span ref={ref} className={`count-up ${className || ''}`} aria-label={final}><span aria-hidden="true">{text}</span></span>;
}

// "33.5%" -> <CountUp value={33.5} decimals={1} suffix="%" />; anything non-numeric is returned as is.
export function AnimatedValue({ value }) {
  const match = String(value).match(/^([^\d-]*)(-?\d+(?:\.(\d+))?)(.*)$/);
  if (!match) return value;
  return <CountUp prefix={match[1]} value={Number(match[2])} decimals={match[3]?.length || 0} suffix={match[4]} />;
}
