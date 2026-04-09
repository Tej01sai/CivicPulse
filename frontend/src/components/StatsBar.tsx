import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { DashboardStats } from '../lib/api';

const statConfigs = [
  { key: 'total_open_needs',     label: 'Open Needs',      cls: 'blue',     icon: '📌' },
  { key: 'critical_needs',       label: 'Critical',         cls: 'critical', icon: '🔴' },
  { key: 'high_needs',           label: 'High Priority',    cls: 'high',     icon: '🟠' },
  { key: 'total_volunteers',     label: 'Volunteers',       cls: 'green',    icon: '🙋' },
  { key: 'total_assignments',    label: 'Assignments',      cls: 'blue',     icon: '📋' },
  { key: 'match_success_rate',   label: 'Match Rate',       cls: 'green',    icon: '⭐', suffix: '%' },
];

export default function StatsBar() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="stats-bar">
      {statConfigs.map(s => (
        <div key={s.key} className="stat-card" style={{ opacity: 0.5 }}>
          <div className="stat-label">{s.label}</div>
          <div className="stat-value">—</div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="stats-bar">
      {statConfigs.map(s => (
        <div key={s.key} className="stat-card">
          <div className="stat-label">{s.icon} {s.label}</div>
          <div className={`stat-value ${s.cls}`}>
            {stats ? (stats as any)[s.key] : '—'}{s.suffix || ''}
          </div>
        </div>
      ))}
    </div>
  );
}
