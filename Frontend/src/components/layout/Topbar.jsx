import { Bell, ChevronDown, LogOut, Menu, Search, UserRound } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LanguageToggle } from '../../i18n';
import { ThemeToggle } from '../../ui/theme';

export default function Topbar({ onMenu, onSearch }) {
    const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
    const { user, logout } = useAuth();
    const [menuOpen, setMenuOpen] = useState(false);
    const initials = user?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() || 'CG';
  return (
    <header className="topbar">
      <button className="icon-btn mobile-only" onClick={onMenu} aria-label="Open navigation"><Menu size={21} /></button>
      <button type="button" className="topbar-search" onClick={onSearch} aria-label="Search pages and actions"><Search size={18} /><span>Search or jump to…</span><kbd>{isMac ? '⌘' : 'Ctrl'} K</kbd></button>
      <div className="topbar-actions">
        <LanguageToggle />
        <ThemeToggle />
        <button className="icon-btn notification-btn" aria-label="Notifications"><Bell size={19} /><span /></button>
          <div className="profile-wrap"><button className="profile-chip" onClick={() => setMenuOpen((value) => !value)}><span className="avatar">{initials}</span><span className="profile-name"><strong>{user?.name}</strong><small>Personal workspace</small></span><ChevronDown size={15} /></button>{menuOpen && <div className="profile-menu"><Link to="/profile"><UserRound size={15} /> My profile</Link><Link to="/settings"><UserRound size={15} /> Settings</Link><button onClick={logout}><LogOut size={15} /> Log out</button></div>}</div>
      </div>
    </header>
  );
}