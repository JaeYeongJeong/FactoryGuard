import type { DetectionEvent, IncidentReport, RagResult } from "./types";

export const API_URL = (import.meta.env.VITE_API_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");
export const AI_URL = (import.meta.env.VITE_API_AI_URL || "http://localhost:8001").replace(/\/$/, "");
export const EVENT_WS_URL = (import.meta.env.VITE_EVENT_WS_URL || API_URL.replace(/^http/, "ws")).replace(/\/$/, "");
export const AI_WS_URL = (import.meta.env.VITE_AI_WS_URL || AI_URL.replace(/^http/, "ws")).replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "요청을 처리하지 못했습니다.");
  return body as T;
}

export async function getEvents(limit = 100) {
  return (await request<{ events: DetectionEvent[] }>(`/events?limit=${limit}`)).events;
}

export async function updateEvent(eventId: string, status: string, responseMemo: string) {
  return (await request<{ event: DetectionEvent }>(`/events/${encodeURIComponent(eventId)}`, {
    method: "PATCH",
    body: JSON.stringify({ response_status: status, response_memo: responseMemo }),
  })).event;
}

export async function getReports(limit = 50) {
  return (await request<{ reports: IncidentReport[] }>(`/reports?limit=${limit}`)).reports;
}

export async function analyzeEvent(eventId: string) {
  return request<Record<string, unknown>>(`/reports/analyze-event/${encodeURIComponent(eventId)}`, { method: "POST" });
}

export async function searchRag(payload: Record<string, unknown>) {
  return request<RagResult>("/rag/search", { method: "POST", body: JSON.stringify(payload) });
}

export async function simulateKws(payload: Record<string, unknown>) {
  return request<Record<string, any>>("/kws/simulate", { method: "POST", body: JSON.stringify(payload) });
}
