import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { getEvents, getReports, updateEvent } from "./api";
import Sidebar, { type Page } from "./components/Sidebar";
import { useEventStream } from "./hooks/useEventStream";
import Dashboard from "./pages/Dashboard";
import EventResponse from "./pages/EventResponse";
import History from "./pages/History";
import Kws from "./pages/Kws";
import Monitoring from "./pages/Monitoring";
import Rag from "./pages/Rag";
import Report from "./pages/Report";
import type { DetectionEvent, IncidentReport } from "./types";

function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [events, setEvents] = useState<DetectionEvent[]>([]);
  const [reports, setReports] = useState<IncidentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const refresh = useCallback(async () => {
    setError("");
    const [eventResult, reportResult] = await Promise.allSettled([getEvents(), getReports()]);
    if (eventResult.status === "fulfilled") setEvents(eventResult.value);
    if (reportResult.status === "fulfilled") setReports(reportResult.value);
    if (eventResult.status === "rejected" || reportResult.status === "rejected") setError("서버 데이터 일부를 불러오지 못했습니다.");
    setLoading(false);
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  const receiveEvent = useCallback((event: DetectionEvent) => {
    setEvents((current) => [event, ...current.filter((item) => item.event_id !== event.event_id)].slice(0, 200));
  }, []);
  const streamStatus = useEventStream(receiveEvent);

  const saveResponse = async (eventId: string, status: string, memo: string) => {
    const updated = await updateEvent(eventId, status, memo);
    setEvents((current) => current.map((item) => item.event_id === eventId ? updated : item));
  };

  const navigate = (next: Page) => { setPage(next); setMenuOpen(false); };

  return (
    <div className="app">
      <Sidebar setPage={navigate} currentPage={page} streamStatus={streamStatus} open={menuOpen} close={() => setMenuOpen(false)} />
      <main className="main-content">
        <header className="mobile-header">
          <button className="icon-btn" onClick={() => setMenuOpen(true)} aria-label="메뉴 열기">☰</button>
          <strong>LineShield</strong>
          <span className={`connection-dot ${streamStatus}`} title="이벤트 스트림 상태" />
        </header>
        {error && <div className="error-banner">{error}<button onClick={() => void refresh()}>다시 시도</button></div>}
        {page === "dashboard" && <Dashboard events={events} loading={loading} />}
        {page === "monitoring" && <Monitoring />}
        {page === "event" && <EventResponse events={events} saveResponse={saveResponse} />}
        {page === "history" && <History events={events} />}
        {page === "report" && <Report events={events} reports={reports} onCreated={refresh} />}
        {page === "rag" && <Rag />}
        {page === "kws" && <Kws onDetected={receiveEvent} />}
      </main>
    </div>
  );
}

export default App;
