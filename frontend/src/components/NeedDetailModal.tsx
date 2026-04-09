import { useEffect, useState } from 'react';
import type { Need, Volunteer } from '../lib/api';
import { api } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';

interface Props {
  need: Need;
  onClose: () => void;
  onAssigned?: () => void;
}



export default function NeedDetailModal({ need, onClose, onAssigned }: Props) {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [assigned, setAssigned] = useState<string | null>(null);
  const [alerting, setAlerting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all volunteers for listing (simplified: no match endpoint on volunteers page for now)
  useEffect(() => {
    api.getVolunteers().then(setVolunteers).catch(() => {});
  }, []);

  const handleAssign = async (volunteerId: string) => {
    setAssigning(volunteerId);
    setError(null);
    try {
      await api.createAssignment(need.id, volunteerId);
      setAssigned(volunteerId);
      onAssigned?.();
    } catch (e: any) {
      setError(e.message || 'Assignment failed');
    } finally {
      setAssigning(null);
    }
  };

  const handleAlert = async () => {
    setAlerting(true);
    try {
      await api.triggerAlert(need.id);
    } catch (e) {
      setError('Alert failed');
    } finally {
      setAlerting(false);
    }
  };

  const urgColor = need.urgency === 'CRITICAL' ? 'var(--critical)'
    : need.urgency === 'HIGH' ? 'var(--high)'
    : need.urgency === 'MEDIUM' ? 'var(--medium)'
    : 'var(--low)';

  return (
    <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        {/* Header */}
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 6 }}>
              <span className="need-type-badge" style={{
                background: `${urgColor}22`,
                color: urgColor,
                fontSize: 12, fontWeight: 700, letterSpacing: '0.05em',
                padding: '4px 12px', borderRadius: 999,
              }}>
                {need.need_type}
              </span>
              <span style={{
                fontSize: 12, fontWeight: 700, letterSpacing: '0.08em',
                color: urgColor, background: `${urgColor}18`,
                padding: '3px 10px', borderRadius: 999,
              }}>
                {need.urgency}
              </span>
              {need.report_count && need.report_count > 1 && (
                <span style={{ fontSize: 12, color: 'var(--accent-cyan)' }}>
                  📑 {need.report_count} duplicate reports
                </span>
              )}
            </div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>
              {need.need_subtype || need.need_type || 'Community Need'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
              {need.location_district && `📍 ${need.location_district}`}
              {need.location_address && ` · ${need.location_address}`}
              {need.created_at && ` · ${formatDistanceToNow(new Date(need.created_at), { addSuffix: true })}`}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Original report */}
          {need.raw_input && (
            <div style={{ marginBottom: 20 }}>
              <div className="section-title">📝 Original Report</div>
              <div style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px 16px',
                fontSize: 14,
                color: 'var(--text-secondary)',
                fontStyle: 'italic',
                lineHeight: 1.6,
              }}>
                "{need.raw_input}"
              </div>
            </div>
          )}

          {/* Key details grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
            {[
              { label: '👥 Affected', value: need.affected_population != null ? `${need.affected_population} person(s)` : '—' },
              { label: '⏱ Effort', value: need.estimated_effort_hours ? `${need.estimated_effort_hours}h` : '—' },
              { label: '⚡ Urgency Reason', value: need.urgency_reason || '—' },
              { label: '🔧 Resource Gaps', value: need.resource_gaps || '—' },
              { label: '📊 Priority Score', value: need.urgency_score != null ? `${Math.round(need.urgency_score * 100)}/100` : '—' },
              { label: '🎯 Confidence', value: need.confidence_score != null ? `${Math.round(need.confidence_score * 100)}%` : '—' },
            ].map(({ label, value }) => (
              <div key={label} style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
              }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 14, color: 'var(--text-primary)' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Skills needed */}
          {need.skills_needed && need.skills_needed.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div className="section-title">🛠 Skills Needed</div>
              <div className="skill-tags">
                {need.skills_needed.map(s => (
                  <span key={s} className="skill-tag">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* AI Recommendations */}
          {need.recommendations && (
            <div style={{ marginBottom: 24 }}>
              <div className="section-title">🤖 AI Recommendations</div>
              <div style={{
                background: 'rgba(59,130,246,0.08)',
                border: '1px solid rgba(59,130,246,0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 18px',
                fontSize: 14,
                color: 'var(--text-secondary)',
                lineHeight: 1.7,
              }}>
                {need.recommendations}
              </div>
            </div>
          )}

          {/* Volunteer assignment */}
          {need.status === 'open' && (
            <div>
              <div className="section-title">👤 Assign a Volunteer</div>
              {error && (
                <div style={{ color: 'var(--critical)', fontSize: 13, marginBottom: 10 }}>⚠ {error}</div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 240, overflowY: 'auto' }}>
                {volunteers.slice(0, 10).map(vol => {
                  const isAssigned = assigned === vol.id;
                  return (
                    <div key={vol.id} style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      background: isAssigned ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.03)',
                      border: `1px solid ${isAssigned ? 'rgba(16,185,129,0.4)' : 'var(--border)'}`,
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px 14px',
                      transition: 'all 0.2s',
                    }}>
                      <div className="volunteer-avatar" style={{ width: 36, height: 36, fontSize: 13 }}>
                        {vol.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{vol.name}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {vol.skills_list?.slice(0, 3).join(', ')}
                        </div>
                      </div>
                      {vol.average_rating ? (
                        <span style={{ fontSize: 12, color: '#fbbf24' }}>
                          ★ {vol.average_rating.toFixed(1)}
                        </span>
                      ) : null}
                      <button
                        className="btn btn-sm btn-primary"
                        disabled={isAssigned || assigning === vol.id || assigned !== null}
                        onClick={() => handleAssign(vol.id)}
                      >
                        {isAssigned ? '✓ Assigned' : assigning === vol.id ? '...' : 'Assign'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {need.status !== 'open' && (
            <div style={{
              textAlign: 'center', padding: '20px',
              color: 'var(--accent-green)', fontSize: 15, fontWeight: 600,
            }}>
              ✅ This need has been {need.status}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          {need.status === 'open' && (
            <button
              className="btn btn-danger btn-sm"
              onClick={handleAlert}
              disabled={alerting}
            >
              {alerting ? '...' : '🚨 Send Alert'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
