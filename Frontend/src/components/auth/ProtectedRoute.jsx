import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function ProtectedRoute() {
  const { user, checking } = useAuth();
  const location = useLocation();
  if (checking) return <div className="auth-loading"><div className="loading-spinner" /><span>Checking your workspace...</span></div>;
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}