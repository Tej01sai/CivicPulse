import { NavLink } from 'react-router-dom';
import { useAlerts } from '../hooks/useAlerts';

const navItems = [
  { to: '/',            icon: '📊', label: 'Dashboard' },
  { to: '/intake',      icon: '📋', label: 'Data Intake' },
  { to: '/volunteers',  icon: '🙋', label: 'Volunteers' },
  { to: '/assignments', icon: '✅', label: 'Assignments' },
];

interface SidebarProps {
  criticalCount?: number;
}

export default function Sidebar({ criticalCount = 0 }: SidebarProps) {
  const { connected } = useAlerts();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🏙️</div>
        <span className="sidebar-logo-text">CivicPulse</span>
      </div>

      <span className="nav-section-label">Navigation</span>
      {navItems.map(item => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          <span className="nav-icon">{item.icon}</span>
          <span>{item.label}</span>
          {item.to === '/' && criticalCount > 0 && (
            <span className="nav-badge">{criticalCount}</span>
          )}
        </NavLink>
      ))}

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: connected ? 'var(--accent-green)' : 'var(--critical)',
            display: 'inline-block',
          }} />
          <span>{connected ? 'Live' : 'Reconnecting...'}</span>
        </div>
        <div style={{ opacity: 0.6 }}>Phase 1 MVP</div>
      </div>
    </aside>
  );
}
