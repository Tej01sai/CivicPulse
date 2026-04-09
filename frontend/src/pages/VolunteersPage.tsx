import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Volunteer } from '../lib/api';

export default function VolunteersPage() {
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: '', email: '', phone: '',
    skills_raw: '',
    willing_distance_km: 10,
    transport_available: false,
  });

  useEffect(() => {
    api.getVolunteers()
      .then(setVolunteers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async () => {
    if (!form.name || !form.email || !form.skills_raw) {
      setError('Name, email, and skills are required');
      return;
    }
    setSaving(true); setError(null);
    try {
      const vol = await api.createVolunteer({
        name: form.name, email: form.email, phone: form.phone,
        skills_raw: form.skills_raw,
        willing_distance_km: form.willing_distance_km,
        transport_available: form.transport_available,
        availability: { weekdays: true },
      });
      setVolunteers(prev => [vol, ...prev]);
      setShowForm(false);
      setForm({ name: '', email: '', phone: '', skills_raw: '', willing_distance_km: 10, transport_available: false });
    } catch (e: any) {
      setError(e.message || 'Registration failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 className="page-title">Volunteer Roster</h1>
          <p className="page-subtitle">{volunteers.length} registered volunteers</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(s => !s)}>
          {showForm ? '✕ Cancel' : '+ Register Volunteer'}
        </button>
      </div>

      {/* Registration Form */}
      {showForm && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glow)',
          borderRadius: 'var(--radius-lg)',
          padding: 24,
          marginBottom: 28,
        }}>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 20 }}>🙋 New Volunteer</div>
          {error && <div style={{ color: 'var(--critical)', fontSize: 13, marginBottom: 12 }}>⚠ {error}</div>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { key: 'name',  label: 'Full Name*',    placeholder: 'James Okonkwo' },
              { key: 'email', label: 'Email*',         placeholder: 'james@example.com' },
              { key: 'phone', label: 'Phone',          placeholder: '+1 555 000 0000 (optional)' },
            ].map(f => (
              <div key={f.key} className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{f.label}</label>
                <input
                  className="form-control"
                  placeholder={f.placeholder}
                  value={(form as any)[f.key]}
                  onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                />
              </div>
            ))}
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Willing Distance (km)</label>
              <input
                type="number" className="form-control"
                value={form.willing_distance_km}
                onChange={e => setForm(prev => ({ ...prev, willing_distance_km: Number(e.target.value) }))}
              />
            </div>
          </div>
          <div className="form-group" style={{ marginTop: 16, marginBottom: 0 }}>
            <label className="form-label">Skills (free-form)*</label>
            <textarea
              className="form-control"
              style={{ minHeight: 80 }}
              placeholder="e.g. I do carpentry, have built decks and renovated roofs. Also comfortable with basic plumbing. Available weekends."
              value={form.skills_raw}
              onChange={e => setForm(prev => ({ ...prev, skills_raw: e.target.value }))}
            />
            <div className="form-hint">Describe your skills naturally — AI will embed them for semantic matching</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, marginBottom: 20 }}>
            <input
              id="transport"
              type="checkbox"
              checked={form.transport_available}
              onChange={e => setForm(prev => ({ ...prev, transport_available: e.target.checked }))}
            />
            <label htmlFor="transport" style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              I have a vehicle and can provide transport
            </label>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
              {saving ? 'Registering...' : '✓ Register Volunteer'}
            </button>
            <button className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Volunteer List */}
      {loading ? (
        <div className="loading-center"><span className="spinner" /> Loading volunteers...</div>
      ) : volunteers.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🙋</div>
          <div className="empty-state-title">No volunteers yet</div>
          <div className="empty-state-body">Run seed_data.py or register a volunteer above</div>
        </div>
      ) : (
        <div className="volunteer-list">
          {volunteers.map(vol => (
            <div key={vol.id} className="volunteer-card">
              <div className="volunteer-avatar">
                {vol.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div style={{ flex: 1 }}>
                <div className="volunteer-name">{vol.name}</div>
                <div className="volunteer-skills">
                  {vol.skills_list?.slice(0, 5).join(' · ') || vol.skills_raw?.slice(0, 60)}
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  {vol.transport_available && (
                    <span className="meta-tag">🚗 Transport</span>
                  )}
                  {vol.willing_distance_km && (
                    <span className="meta-tag">📍 {vol.willing_distance_km}km range</span>
                  )}
                  {vol.total_tasks_completed ? (
                    <span className="meta-tag">✅ {vol.total_tasks_completed} tasks</span>
                  ) : null}
                </div>
              </div>
              <div className="volunteer-stats">
                {vol.average_rating ? (
                  <div className="star-rating">★ {vol.average_rating.toFixed(1)}</div>
                ) : <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>No rating yet</div>}
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  {vol.email}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
