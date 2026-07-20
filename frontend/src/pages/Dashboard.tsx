import { Activity, AlertTriangle, CheckCircle2, ShieldAlert, Users } from "lucide-react";
import { eventLabel, severityLabel, statusLabel } from "../labels";
import type { HistoryPreset } from "./History";
import type { DetectionEvent } from "../types";

function Dashboard({ events, loading, onOpenHistory }: { events: DetectionEvent[]; loading: boolean; onOpenHistory: (preset: HistoryPreset) => void }) {
  const critical = events.filter((event) => event.severity === "critical").length;
  const unresolved = events.filter((event) => !["resolved", "false_positive"].includes(event.response_status || "") && event.status !== "exited").length;
  const workers = new Set(events.filter((event) => event.worker_id > 0).map((event) => event.worker_id)).size;
  return <div><div className="page-heading"><div><h1>관리자 대시보드</h1><p className="page-desc">공장 위험 감지와 현장 조치 상태를 실시간으로 확인합니다.</p></div><span className="live-chip"><Activity size={15}/> LIVE</span></div>
    <div className="cards">
      <button className="card" onClick={() => onOpenHistory("all")}><Activity/><h2>{events.length}</h2><p>전체 감지 이벤트</p><small>전체 이력 보기</small></button>
      <button className="card critical" onClick={() => onOpenHistory("critical")}><AlertTriangle/><h2>{critical}</h2><p>긴급 위험</p><small>매우 높은 위험만 보기</small></button>
      <button className="card warning" onClick={() => onOpenHistory("unresolved")}><ShieldAlert/><h2>{unresolved}</h2><p>확인 필요</p><small>미조치 사건 보기</small></button>
      <button className="card" onClick={() => onOpenHistory("workers")}><Users/><h2>{workers}</h2><p>감지 작업자</p><small>작업자 사건 보기</small></button>
    </div>
    <section className="panel"><div className="panel-header"><h2>최근 감지 이력</h2><span>{loading ? "불러오는 중" : `${events.length}건`}</span></div>
      {!loading && events.length === 0 ? <div className="empty-state"><CheckCircle2/><p>현재 감지된 이벤트가 없습니다.</p></div> : <div className="table-scroll"><table><thead><tr><th>발생 시각</th><th>위험 유형</th><th>구역</th><th>위험도</th><th>조치 상태</th></tr></thead><tbody>{events.slice(0, 8).map((event) => <tr key={event.event_id}><td>{new Date(event.timestamp).toLocaleString("ko-KR")}</td><td>{eventLabel(event.event_type)}</td><td>{event.zone_name}</td><td><span className={`badge ${event.severity}`}>{severityLabel(event.severity)}</span></td><td><span className={`action-status ${event.response_status || "pending"}`}>{statusLabel(event.response_status || event.status)}</span></td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}
export default Dashboard;
