import { useEffect, useState } from 'react';
import { getHistory } from '../services/api';

export default function useHistoryData() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    getHistory().then((data) => { if (active) setHistory(data); }).catch(() => { if (active) setError('We could not load your private health history.'); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return { history, loading, error };
}
