import type { Need } from '../lib/api';
import { formatDistanceToNow } from 'date-fns';

interface NeedCardProps {
  need: Need;
  onClick: (need: Need) => void;
}

function getUrgencyClass(urgency?: string) {
  const u = (urgency || '').toLowerCase();
  if (u === 'critical') return 'critical';
  if (u === 'high') return 'high';
  if (u === 'medium') return 'medium';
  return 'low';
}

function getUrgencyDot(urgency?: string) {
  const u = (urgency || '').toLowerCase();
  if (u === 'critical') return '🔴';
  if (u === 'high') return '🟠';
  if (u === 'medium') return '🟡';
  return '🟢';
}

function scoreColor(score: number) {
  if (score >= 0.75) return 'var(--critical)';
  if (score >= 0.5)  return 'var(--high)';
  if (score >= 0.3)  return 'var(--medium)';
  return 'var(--low)';
}

export default function NeedCard({ need, onClick }: NeedCardProps) {
  const cls = getUrgencyClass(need.urgency);
  const score = need.urgency_score ?? 0;
  const timeAgo = need.created_at
    ? formatDistanceToNow(new Date(need.created_at), { addSuffix: true })
    : '';

  return (
    <div
      className={`need-card ${cls}`}
      onClick={() => onClick(need)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick(need)}
    >
      <div className="need-card-header">
        <span className="need-type-badge">{need.need_type || 'Unknown'}</span>
        <span className="urgency-badge">
          {getUrgencyDot(need.urgency)} {need.urgency}
        </span>
      </div>

      <div className="need-card-body">
        {need.urgency_reason || need.raw_input || 'No description'}
      </div>

      <div className="need-card-meta">
        {need.location_district && (
          <span className="meta-tag">📍 {need.location_district}</span>
        )}
        {need.affected_population != null && need.affected_population > 0 && (
          <span className="meta-tag">👥 {need.affected_population} affected</span>
        )}
        {need.estimated_effort_hours && (
          <span className="meta-tag">⏱ {need.estimated_effort_hours}h</span>
        )}
        {(need.report_count ?? 1) > 1 && (
          <span className="meta-tag" style={{ color: 'var(--accent-cyan)' }}>
            📑 {need.report_count} reports
          </span>
        )}
      </div>

      {need.skills_needed && need.skills_needed.length > 0 && (
        <div className="skill-tags" style={{ marginBottom: 12 }}>
          {need.skills_needed.slice(0, 3).map(s => (
            <span key={s} className="skill-tag">{s}</span>
          ))}
          {need.skills_needed.length > 3 && (
            <span className="skill-tag">+{need.skills_needed.length - 3}</span>
          )}
        </div>
      )}

      <div className="need-card-footer">
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{timeAgo}</span>
        <div className="score-bar-wrap">
          <div className="score-label">Priority Score</div>
          <div className="score-bar">
            <div
              className="score-fill"
              style={{ width: `${Math.round(score * 100)}%`, background: scoreColor(score) }}
            />
          </div>
        </div>
        <span style={{ fontSize: 12, fontWeight: 700, color: scoreColor(score) }}>
          {Math.round(score * 100)}
        </span>
      </div>
    </div>
  );
}
