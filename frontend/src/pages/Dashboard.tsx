import { Activity, AlertTriangle, CheckCircle2, ShieldAlert, Users } from "lucide-react";
import { eventLabel, severityLabel, statusLabel } from "../labels";
import type { DetectionEvent } from "../types";

function Dashboard({ events, loading }: { events: DetectionEvent[]; loading: boolean }) {
  const critical = events.filter((e) => e.severity === "critical").length;
  const unresolved = events.filter((e) => !["resolved", "false_positive"].includes(e.response_status || "") && e.status !== "exited").length;
  const workers = new Set(events.map((e) => e.worker_id)).size;
  return <div><div className="page-heading"><div><h1>관리자 대시보드</h1><p className="page-desc">공장 위험 감지와 현장 조치 상태를 실시간으로 확인합니다.</p></div><span className="live-chip"><Activity size={15}/> LIVE</span></div>
    <div className="cards">
      <div className="card"><Activity/><h2>{events.length}</h2><p>전체 감지 이벤트</p></div>
      <div className="card critical"><AlertTriangle/><h2>{critical}</h2><p>긴급 위험</p></div>
      <div className="card warning"><ShieldAlert/><h2>{unresolved}</h2><p>확인 필요</p></div>
      <div className="card"><Users/><h2>{workers}</h2><p>감지 작업자</p></div>
    </div>
    <section className="panel"><div className="panel-header"><h2>최근 감지 이력</h2><span>{loading ? "불러오는 중" : `${events.length}건`}</span></div>
      {!loading && events.length === 0 ? <div className="empty-state"><CheckCircle2/><p>현재 감지된 이벤트가 없습니다.</p></div> : <div className="table-scroll"><table><thead><tr><th>발생 시각</th><th>위험 유형</th><th>구역</th><th>위험도</th><th>조치 상태</th></tr></thead><tbody>{events.slice(0, 8).map((e) => <tr key={e.event_id}><td>{new Date(e.timestamp).toLocaleString("ko-KR")}</td><td>{eventLabel(e.event_type)}</td><td>{e.zone_name}</td><td><span className={`badge ${e.severity}`}>{severityLabel(e.severity)}</span></td><td>{statusLabel(e.response_status || e.status)}</td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}
export default Dashboard;
