// API client for CivicPulse backend
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Need {
  id: string;
  raw_input?: string;
  need_type?: string;
  need_subtype?: string;
  location_address?: string;
  location_district?: string;
  urgency?: string;
  urgency_reason?: string;
  skills_needed?: string[];
  affected_population?: number;
  resource_gaps?: string;
  estimated_effort_hours?: number;
  escalation_risk?: number;
  urgency_score?: number;
  confidence_score?: number;
  status?: string;
  report_count?: number;
  duplicate_of?: string;
  created_at?: string;
  recommendations?: string;
}

export interface NeedListResponse {
  total: number;
  needs: Need[];
}

export interface Volunteer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  skills_raw?: string;
  skills_list?: string[];
  availability?: Record<string, boolean>;
  transport_available?: boolean;
  latitude?: number;
  longitude?: number;
  willing_distance_km?: number;
  total_tasks_completed?: number;
  average_rating?: number;
  created_at?: string;
}

export interface MatchResult {
  need_id: string;
  need_type?: string;
  urgency?: string;
  location_district?: string;
  location_address?: string;
  skills_needed?: string[];
  affected_population?: number;
  estimated_effort_hours?: number;
  urgency_score?: number;
  match_score: number;
  skill_similarity: number;
  status?: string;
  created_at?: string;
}

export interface Assignment {
  id: string;
  need_id: string;
  volunteer_id: string;
  status: string;
  match_score?: number;
  outcome_notes?: string;
  volunteer_rating?: number;
  assigned_at?: string;
  completed_at?: string;
}

export interface DashboardStats {
  total_open_needs: number;
  critical_needs: number;
  high_needs: number;
  resolved_total: number;
  total_volunteers: number;
  total_assignments: number;
  match_success_rate: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Needs ────────────────────────────────────────────────────────────────────
export const api = {
  // Needs
  getNeeds: (params: { urgency?: string; district?: string; status?: string; skip?: number; limit?: number } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return request<NeedListResponse>(`/needs?${q}`);
  },
  getNeed: (id: string, includeRecs = true) =>
    request<Need>(`/needs/${id}?include_recommendations=${includeRecs}`),

  // Intake
  parseText: (text: string) =>
    request<Need>('/intake/parse', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  parseImage: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE_URL}/intake/parse-image`, { method: 'POST', body: form }).then(r => r.json() as Promise<Need>);
  },

  // Volunteers
  getVolunteers: () => request<Volunteer[]>('/volunteers'),
  getVolunteer: (id: string) => request<Volunteer>(`/volunteers/${id}`),
  createVolunteer: (body: Partial<Volunteer> & { skills_raw: string }) =>
    request<Volunteer>('/volunteers', { method: 'POST', body: JSON.stringify(body) }),
  getMatches: (volunteerId: string, topK = 5) =>
    request<MatchResult[]>(`/matches/${volunteerId}?top_k=${topK}`),

  // Assignments
  getAssignments: (status?: string) =>
    request<Assignment[]>(`/assignments${status ? `?status=${status}` : ''}`),
  createAssignment: (needId: string, volunteerId: string) =>
    request<Assignment>('/assignments', {
      method: 'POST',
      body: JSON.stringify({ need_id: needId, volunteer_id: volunteerId }),
    }),
  completeAssignment: (id: string, outcomeNotes?: string, rating?: number) =>
    request<Assignment>(`/assignments/${id}/complete`, {
      method: 'PUT',
      body: JSON.stringify({ outcome_notes: outcomeNotes, volunteer_rating: rating }),
    }),

  // Alerts
  triggerAlert: (needId: string) =>
    request(`/alerts/trigger/${needId}`, { method: 'POST' }),
  getStats: () => request<DashboardStats>('/alerts/stats'),
};
