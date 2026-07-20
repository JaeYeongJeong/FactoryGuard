import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { eventLabel, severityLabel, statusLabel } from "../labels";
import type { DetectionEvent } from "../types";

function History({ events }: { events: DetectionEvent[] }) {
  const [query, setQuery] = useState(""); const [severity, setSeverity] = useState("all");
  const filtered = useMemo(() => events.filter((e) => (severity === "all" || e.severity === severity) && `${e.message} ${e.zone_name} ${eventLabel(e.event_type)}`.toLowerCase().includes(query.toLowerCase())), [events, query, severity]);
  return <div><div className="page-heading"><div><h1>감지 이력</h1><p className="page-desc">저장된 위험 이벤트를 검색하고 필터링합니다.</p></div></div><section className="panel"><div className="filter-bar"><label className="search-field"><Search size={17}/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="위험 유형, 구역, 내용 검색"/></label><select value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="all">전체 위험도</option><option value="critical">매우 높음</option><option value="high">높음</option><option value="medium">중간</option><option value="low">낮음</option></select><span>{filtered.length}건</span></div><div className="table-scroll"><table><thead><tr><th>발생 시각</th><th>위험 유형</th><th>카메라 / 구역</th><th>작업자</th><th>위험도</th><th>상태</th></tr></thead><tbody>{filtered.map((e) => <tr key={e.event_id}><td>{new Date(e.timestamp).toLocaleString("ko-KR")}</td><td>{eventLabel(e.event_type)}</td><td>{e.camera_id}<small className="cell-sub">{e.zone_name}</small></td><td>#{e.worker_id}</td><td><span className={`badge ${e.severity}`}>{severityLabel(e.severity)}</span></td><td>{statusLabel(e.status)}</td></tr>)}</tbody></table></div>{filtered.length === 0 && <div className="empty-state"><p>조건에 맞는 이벤트가 없습니다.</p></div>}</section></div>;
}
export default History;
