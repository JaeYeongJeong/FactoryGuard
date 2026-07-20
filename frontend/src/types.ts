export type DetectionEvent = {
  event_id: string;
  camera_id: string;
  timestamp: string;
  last_seen_at?: string | null;
  exited_at?: string | null;
  duration?: number;
  event_type: string;
  severity: string;
  status: string;
  response_status?: string | null;
  worker_id: number;
  zone_name: string;
  message: string;
  snapshot_url?: string | null;
  response_memo?: string | null;
};

export type IncidentReport = {
  report_id: string;
  event_id?: string | null;
  source: string;
  created_at: string;
  report: string;
  legal_basis: Array<Record<string, unknown>>;
  recommended_action: string[];
  rag_available: boolean;
};

export type RagResult = {
  query: string;
  inferred_hazard_tags: string[];
  results: Array<{
    chunk_id: string;
    rank: number;
    adjusted_score: number;
    section?: string | null;
    source_filename?: string | null;
    source_pages?: string | number | null;
    text: string;
    parent_text?: string | null;
  }>;
};
