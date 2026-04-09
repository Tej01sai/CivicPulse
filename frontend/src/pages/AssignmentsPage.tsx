import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Assignment } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';

const STATUS_COLORS: Record<string, string> = {
  pending:   'var(--medium)',
  completed: 'var(--accent-green)',
  cancelled: 'var(--critical)',
};

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState<string | null>(null);
  const [outcomeNotes, setOutcomeNotes] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    api.getAssignments()
      .then(setAssignments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleComplete = async (id: string) => {
    setCompleting(id);
    try {
      const updated = await api.completeAssignment(id, outcomeNotes[id], 5.0);
      setAssignments(prev => prev.map(a => a.id === id ? updated : a));
    } catch { /* show error */ }
    finally { setCompleting(null); }
  };

  const filtered = assignments.filter(a =>
    filter === 'all' ? true :
    filter === 'active' ? a.status === 'pending' :
    a.status === 'completed'
  );

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Assignments</h1>
        <p className="page-subtitle">{assignments.length} total assignments</p>
      </div>

      <div className="filters-row">
        {[['all', 'All'], ['active', 'In Progress'], ['completed', 'Completed']].map(([val, label]) => (
          <button
            key={val}
            className={`filter-chip ${filter === val ? 'active' : ''}`}
            onClick={() => setFilter(val)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><span className="spinner" /> Loading assignments...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No assignments yet</div>
          <div className="empty-state-body">
            Assign volunteers to needs from the Dashboard or Need Detail modal
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {filtered.map(a => (
            <div key={a.id} style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: '18px 20px',
              transition: 'all 0.2s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12 }}>
                <div style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: STATUS_COLORS[a.status] || 'var(--text-muted)',
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>
                    Assignment #{a.id.slice(0, 8)}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    Need: {a.need_id.slice(0, 8)} · Volunteer: {a.volunteer_id.slice(0, 8)}
                    {a.assigned_at && ` · ${formatDistanceToNow(new Date(a.assigned_at), { addSuffix: true })}`}
                  </div>
                </div>
                <div style={{
                  padding: '4px 10px',
                  borderRadius: 999,
                  fontSize: 11, fontWeight: 700,
                  background: `${STATUS_COLORS[a.status] || 'gray'}18`,
                  color: STATUS_COLORS[a.status] || 'var(--text-muted)',
                }}>
                  {a.status.toUpperCase()}
                </div>
                {a.match_score != null && (
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Match: {Math.round(a.match_score * 100)}%
                  </div>
                )}
              </div>

              {a.outcome_notes && (
                <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 10, paddingLeft: 24 }}>
                  📝 {a.outcome_notes}
                </div>
              )}

              {a.status === 'pending' && (
                <div style={{ paddingLeft: 24, display: 'flex', gap: 10, alignItems: 'center' }}>
                  <input
                    type="text"
                    className="form-control"
                    style={{ flex: 1, maxWidth: 360 }}
                    placeholder="Outcome notes (optional)..."
                    value={outcomeNotes[a.id] || ''}
                    onChange={e => setOutcomeNotes(prev => ({ ...prev, [a.id]: e.target.value }))}
                  />
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => handleComplete(a.id)}
                    disabled={completing === a.id}
                  >
                    {completing === a.id ? '...' : '✅ Mark Complete'}
                  </button>
                </div>
              )}

              {a.completed_at && (
                <div style={{ fontSize: 12, color: 'var(--accent-green)', paddingLeft: 24, marginTop: 6 }}>
                  ✅ Completed {formatDistanceToNow(new Date(a.completed_at), { addSuffix: true })}
                  {a.volunteer_rating && ` · Rating: ${'★'.repeat(Math.round(a.volunteer_rating))}`}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
