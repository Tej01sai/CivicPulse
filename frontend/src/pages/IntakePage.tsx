import { useState, useRef } from 'react';
import { api } from '../lib/api';
import type { Need } from '../lib/api';

export default function IntakePage() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Need | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [mode, setMode] = useState<'text' | 'image'>('text');
  const fileRef = useRef<HTMLInputElement>(null);

  const SAMPLE_TEXT = `Mrs. Chen, elderly woman, 67 years old. Roof started leaking badly 2 weeks ago after heavy rain. Lives at 245 Oak St, Apt 3B, District 5. She's worried about mold developing. On a fixed income and can't afford a contractor. Neighbor Raj offered to help but needs tools and maybe a second pair of hands. The situation will get much worse if it rains again this week.`;

  const handleTextParse = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await api.parseText(text);
      setResult(res);
    } catch (e: any) {
      setError(e.message || 'Failed to parse. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleImageParse = async () => {
    if (!imageFile) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await api.parseImage(imageFile);
      setResult(res);
    } catch (e: any) {
      setError(e.message || 'Image parse failed');
    } finally {
      setLoading(false);
    }
  };

  const urgColor = result?.urgency === 'CRITICAL' ? 'var(--critical)'
    : result?.urgency === 'HIGH' ? 'var(--high)'
    : result?.urgency === 'MEDIUM' ? 'var(--medium)'
    : 'var(--low)';

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Data Intake</h1>
        <p className="page-subtitle">
          Paste field notes or upload a photo — AI extracts structured need data in seconds
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Input Panel */}
        <div>
          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            {(['text', 'image'] as const).map(m => (
              <button
                key={m}
                className={`filter-chip ${mode === m ? 'active' : ''}`}
                onClick={() => { setMode(m); setResult(null); setError(null); }}
              >
                {m === 'text' ? '📝 Field Notes / Text' : '📷 Photo / Image'}
              </button>
            ))}
          </div>

          {mode === 'text' ? (
            <>
              <div className="form-group">
                <label className="form-label">Field Notes or Survey Text</label>
                <textarea
                  className="form-control"
                  style={{ minHeight: 200 }}
                  placeholder="Paste any unstructured field notes, survey responses, SMS reports, or spoken transcripts here..."
                  value={text}
                  onChange={e => setText(e.target.value)}
                />
                <div className="form-hint">
                  Accepts messy text, misspellings, and fragmented notes — Claude will parse it.
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  className="btn btn-primary"
                  onClick={handleTextParse}
                  disabled={loading || !text.trim()}
                >
                  {loading ? <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Parsing...</> : '⚡ Parse with AI'}
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => setText(SAMPLE_TEXT)}
                >
                  Use Sample
                </button>
              </div>
            </>
          ) : (
            <>
              <div
                className="form-group"
                style={{
                  border: '2px dashed var(--border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 40,
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onClick={() => fileRef.current?.click()}
                onDragOver={e => { e.preventDefault(); }}
                onDrop={e => {
                  e.preventDefault();
                  const f = e.dataTransfer.files[0];
                  if (f?.type.startsWith('image/')) setImageFile(f);
                }}
              >
                <div style={{ fontSize: 40, marginBottom: 12 }}>📷</div>
                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>
                  {imageFile ? imageFile.name : 'Drop image or click to browse'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  Supports JPEG, PNG, WebP — survey photos, handwritten notes
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={e => setImageFile(e.target.files?.[0] || null)}
                />
              </div>
              <button
                className="btn btn-primary"
                onClick={handleImageParse}
                disabled={loading || !imageFile}
              >
                {loading ? <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Analyzing...</> : '🔍 Analyze Image'}
              </button>
            </>
          )}

          {error && (
            <div style={{
              marginTop: 16,
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 16px',
              fontSize: 14,
              color: 'var(--critical)',
            }}>
              ⚠ {error}
            </div>
          )}
        </div>

        {/* Output Panel */}
        <div>
          <div className="form-label" style={{ marginBottom: 14 }}>Extracted Output</div>

          {!result && !loading && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: 40,
              textAlign: 'center',
              color: 'var(--text-muted)',
            }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>🧠</div>
              <div style={{ fontSize: 14 }}>Claude 3.5 Sonnet will extract structured data from your input and display it here</div>
            </div>
          )}

          {loading && (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glow)',
              borderRadius: 'var(--radius-lg)',
              padding: 60,
              textAlign: 'center',
            }}>
              <div style={{ marginBottom: 16 }}>
                <span className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
              </div>
              <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>Claude is processing your input...</div>
            </div>
          )}

          {result && !loading && (
            <div>
              {/* Summary card */}
              <div style={{
                background: `${urgColor}12`,
                border: `1px solid ${urgColor}44`,
                borderRadius: 'var(--radius-lg)',
                padding: 20,
                marginBottom: 16,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <span style={{
                    background: `${urgColor}25`,
                    color: urgColor,
                    padding: '4px 12px',
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: 700,
                  }}>
                    {result.urgency}
                  </span>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{result.need_type}</span>
                  {result.confidence_score && (
                    <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
                      Confidence: {Math.round(result.confidence_score * 100)}%
                    </span>
                  )}
                </div>
                {result.urgency_reason && (
                  <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {result.urgency_reason}
                  </div>
                )}
              </div>

              <div className="section-title">Raw JSON Response</div>
              <div className="json-preview">
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>

              <div style={{ marginTop: 12, fontSize: 13, color: 'var(--accent-green)' }}>
                ✅ Need stored and ranked. View it on the{' '}
                <a href="/" style={{ color: 'var(--accent-blue)' }}>Dashboard →</a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
