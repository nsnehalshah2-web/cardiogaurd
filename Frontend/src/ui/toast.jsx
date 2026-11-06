import { createContext, useCallback, useContext, useState } from 'react';
import { CircleAlert, CircleCheck, Info, X } from 'lucide-react';

const ToastContext = createContext(() => {});
const ICONS = { success: CircleCheck, error: CircleAlert, info: Info };

// Small, polite notifications (announced to screen readers) that dismiss themselves.
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const dismiss = useCallback((id) => setToasts((list) => list.filter((toast) => toast.id !== id)), []);
  const show = useCallback((message, { tone = 'info', duration = 4500 } = {}) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((list) => [...list.slice(-2), { id, message, tone }]);
    setTimeout(() => dismiss(id), duration);
  }, [dismiss]);
  return <ToastContext.Provider value={show}>
    {children}
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.tone] || Info;
        return <div key={toast.id} className={`toast ${toast.tone}`}><Icon size={18} /><span>{toast.message}</span><button type="button" className="icon-btn" onClick={() => dismiss(toast.id)} aria-label="Dismiss"><X size={15} /></button></div>;
      })}
    </div>
  </ToastContext.Provider>;
}

export const useToast = () => useContext(ToastContext);
