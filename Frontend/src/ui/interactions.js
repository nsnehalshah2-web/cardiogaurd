// App-wide micro-interactions, set up once from main.jsx. Everything here is decorative:
// pages work the same without it, and it all switches off for prefers-reduced-motion.

const SPOTLIGHT = '.panel, .stat-card, .feature-card, .bento-card, .model-metric, .community-stat, .assessment-panel, .report-sheet, .symptom, .choice, .upload-trigger, .live-demo';
const REVEAL = [
  '.page-content .page-heading', '.page-content .panel', '.page-content .stat-card', '.page-content .model-metric',
  '.page-content .community-stat', '.page-content .report-sheet', '.page-content .assessment-panel',
  '.page-content .empty-state', '.page-content .history-item', '.landing-page [data-reveal]',
].join(', ');

const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function spotlight() {
  let current = null;
  document.addEventListener('pointermove', (event) => {
    if (event.pointerType !== 'mouse') return;
    const card = event.target.closest?.(SPOTLIGHT);
    if (current && current !== card) current.classList.remove('is-lit');
    current = card;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--mx', `${event.clientX - rect.left}px`);
    card.style.setProperty('--my', `${event.clientY - rect.top}px`);
    card.classList.add('is-lit');
  }, { passive: true });
  document.addEventListener('pointerleave', () => current?.classList.remove('is-lit'));
}

function ripples() {
  document.addEventListener('pointerdown', (event) => {
    if (reducedMotion.matches) return;
    const button = event.target.closest?.('.btn, .choice, .segmented button, .side-link');
    if (!button || button.disabled) return;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 1.6;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.cssText = `width:${size}px;height:${size}px;left:${event.clientX - rect.left - size / 2}px;top:${event.clientY - rect.top - size / 2}px`;
    button.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  });
}

function scrolledHeader() {
  const update = () => { document.documentElement.dataset.scrolled = window.scrollY > 8 ? 'true' : 'false'; };
  window.addEventListener('scroll', update, { passive: true });
  update();
}

// Cards fade and rise into place as they enter the viewport, staggered within each group.
function reveals() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  const scan = () => {
    document.querySelectorAll(REVEAL).forEach((element) => {
      if (element.dataset.revealReady) return;
      element.dataset.revealReady = 'true';
      const siblings = [...(element.parentElement?.children || [])];
      element.style.setProperty('--reveal-delay', `${Math.min(siblings.indexOf(element), 6) * 60}ms`);
      element.classList.add('reveal');
      observer.observe(element);
    });
  };
  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; scan(); });
  }).observe(document.getElementById('root'), { childList: true, subtree: true });
  scan();
}

// Gentle 3D tilt for elements marked data-tilt (landing page only).
function tilt() {
  document.addEventListener('pointermove', (event) => {
    if (event.pointerType !== 'mouse' || reducedMotion.matches) return;
    const card = event.target.closest?.('[data-tilt]');
    document.querySelectorAll('[data-tilt].is-tilting').forEach((other) => {
      if (other !== card) { other.classList.remove('is-tilting'); other.style.transform = ''; }
    });
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    card.classList.add('is-tilting');
    card.style.transform = `perspective(900px) rotateX(${(-y * 5).toFixed(2)}deg) rotateY(${(x * 6).toFixed(2)}deg) translateY(-3px)`;
  }, { passive: true });
}

export function setupInteractions() {
  const motion = () => document.documentElement.classList.toggle('motion-ok', !reducedMotion.matches);
  motion();
  reducedMotion.addEventListener?.('change', motion);
  spotlight();
  ripples();
  scrolledHeader();
  reveals();
  tilt();
}
