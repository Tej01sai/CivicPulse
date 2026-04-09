import { useEffect, useState, useCallback } from 'react';
import { api } from '../lib/api';
import type { Need } from '../lib/api';
import StatsBar from '../components/StatsBar';
import NeedCard from '../components/NeedCard';
import NeedDetailModal from '../components/NeedDetailModal';
import { useAlerts } from '../hooks/useAlerts';
import type { AlertMessage } from '../hooks/useAlerts';

const URGENCY_FILTERS = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const TYPE_FILTERS = ['All Types', 'Housing', 'Food', 'Health', 'Home Repair', 'Mental Health', 'Transport', 'Job Training', 'Other'];

export default function Dashboard() {
  const [needs, setNeeds] = useState<Need[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedNeed, setSelectedNeed] = useState<Need | null>(null);
  const [urgencyFilter, setUrgencyFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All Types');
  const [search, setSearch] = useState('');
  const [alerts, setAlerts] = useState<AlertMessage[]>([]);

  const fetchNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (urgencyFilter !== 'All') params.urgency = urgencyFilter;
      if (typeFilter !== 'All Types') params.need_type = typeFilter;
      const res = await api.getNeeds(params);
      setNeeds(res.needs);
      setTotal(res.total);
    } catch {
      setNeeds([]);
    } finally {
      setLoading(false);
    }
  }, [urgencyFilter, typeFilter]);

  useEffect(() => { fetchNeeds(); }, [fetchNeeds]);

  // Real-time alerts via WebSocket
  const handleAlert = useCallback((msg: AlertMessage) => {
    if (msg.type === 'critical_alert' || msg.type === 'assignment_created') {
      setAlerts(prev => [msg, ...prev].slice(0, 3));
      // Refresh needs feed
      fetchNeeds();
    }
  }, [fetchNeeds]);

  useAlerts(handleAlert);

  const filtered = search
    ? needs.filter(n =>
        (n.need_type || '').toLowerCase().includes(search.toLowerCase()) ||
        (n.location_district || '').toLowerCase().includes(search.toLowerCase()) ||
        (n.raw_input || '').toLowerCase().includes(search.toLowerCase()) ||
        (n.urgency_reason || '').toLowerCase().includes(search.toLowerCase())
      )
    : needs;

  const criticalCount = needs.filter(n => n.urgency === 'CRITICAL').length;

  return (
    <div>
      {/* Live alerts */}
      {alerts.map((alert, i) => (
        <div key={i} className="alert-banner" style={{ marginBottom: 12 }}>
          <span className="alert-banner-icon">🚨</span>
          <span className="alert-banner-text">
            {alert.type === 'critical_alert'
              ? `CRITICAL: ${alert.need_type} in ${alert.district} — ${alert.message?.slice(0, 80)}...`
              : `Assignment: ${alert.volunteer_name} assigned to ${alert.need_type} in ${alert.district}`
            }
          </span>
          <button className="alert-banner-close" onClick={() => setAlerts(a => a.filter((_, j) => j !== i))}>✕</button>
        </div>
      ))}

      <div className="page-header">
        <h1 className="page-title">Community Needs Dashboard</h1>
        <p className="page-subtitle">
          {total} total needs — prioritized by AI urgency score
          {criticalCount > 0 && <span style={{ color: 'var(--critical)', fontWeight: 600 }}> · {criticalCount} critical</span>}
        </p>
      </div>

      <StatsBar />

      {/* Filters */}
      <div className="filters-row">
        <input
          type="text"
          className="search-input"
          placeholder="🔍 Search by type, district, description..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {URGENCY_FILTERS.map(f => (
          <button
            key={f}
            className={`filter-chip ${f.toLowerCase()} ${urgencyFilter === f ? 'active' : ''}`}
            onClick={() => setUrgencyFilter(f)}
          >
            {f === 'CRITICAL' ? '🔴' : f === 'HIGH' ? '🟠' : f === 'MEDIUM' ? '🟡' : f === 'LOW' ? '🟢' : ''} {f}
          </button>
        ))}
      </div>

      <div className="filters-row" style={{ marginTop: -10 }}>
        {TYPE_FILTERS.map(f => (
          <button
            key={f}
            className={`filter-chip ${typeFilter === f ? 'active' : ''}`}
            onClick={() => setTypeFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Needs grid */}
      {loading ? (
        <div className="loading-center">
          <span className="spinner" />
          Loading needs...
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <div className="empty-state-title">No needs found</div>
          <div className="empty-state-body">
            {search ? 'Try adjusting your search or filters.' : 'Add needs via Data Intake or run seed_data.py.'}
          </div>
        </div>
      ) : (
        <div className="needs-grid">
          {filtered.map(need => (
            <NeedCard key={need.id} need={need} onClick={setSelectedNeed} />
          ))}
        </div>
      )}

      {selectedNeed && (
        <NeedDetailModal
          need={selectedNeed}
          onClose={() => setSelectedNeed(null)}
          onAssigned={fetchNeeds}
        />
      )}
    </div>
  );
}
