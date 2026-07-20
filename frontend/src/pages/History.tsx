import { FileText, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { eventLabel, statusLabel } from "../labels";
import type { DetectionEvent } from "../types";

export type HistoryPreset = "all" | "critical" | "unresolved" | "workers";
type Props = { events: DetectionEvent[]; preset: HistoryPreset; onRespond: (event: DetectionEvent) => void; onReport: (event: DetectionEvent) => void };

function History({ events, preset, onRespond, onReport }: Props) {
  const [query, setQuery] = useState(""); const [severity, setSeverity] = useState("all");
  useEffect(() => { setQuery(""); setSeverity(preset === "critical" ? "critical" : "all"); }, [preset]);
  const filtered = useMemo(() => events.filter((event) => {
    const matchesSeverity = severity === "all" || event.severity === severity;
    const matchesPreset = preset === "unresolved"
      ? !["resolved", "false_positive"].includes(event.response_status || "") && event.status !== "exited"
      : preset === "workers" ? event.worker_id > 0 : true;
    return matchesSeverity && matchesPreset && `${event.message} ${event.zone_name} ${eventLabel(event.event_type)}`.toLowerCase().includes(query.toLowerCase());
  }), [events, preset, query, severity]);
  return <div><div className="page-heading"><div><h1>감지 이력</h1><p className="page-desc">행을 선택하면 이벤트 응답으로 이동하고, 리포트 버튼은 캡처 분석으로 이동합니다.</p></div></div><section className="panel"><div className="filter-bar"><label className="search-field"><Search size={17}/><input value={query} onChange={(change) => setQuery(change.target.value)} placeholder="위험 유형, 구역, 내용 검색"/></label><select value={severity} onChange={(change) => setSeverity(change.target.value)}><option value="all">전체 위험도</option><option value="critical">매우 높음</option><option value="high">높음</option><option value="medium">중간</option><option value="low">낮음</option></select><span>{filtered.length}건</span></div><div className="table-scroll"><table><thead><tr><th>발생 시각</th><th>위험 유형</th><th>카메라 / 구역</th><th>작업자</th><th>감지 상태</th><th>조치 상태</th><th>리포트</th></tr></thead><tbody>{filtered.map((event) => <tr className="clickable-row" key={event.event_id} onClick={() => onRespond(event)} onKeyDown={(key) => { if (key.key === "Enter" || key.key === " ") onRespond(event); }} tabIndex={0}><td>{new Date(event.timestamp).toLocaleString("ko-KR")}</td><td>{eventLabel(event.event_type)}</td><td>{event.camera_id}<small className="cell-sub">{event.zone_name}</small></td><td>#{event.worker_id}</td><td>{statusLabel(event.status)}</td><td><span className={`action-status ${event.response_status || "pending"}`}>{statusLabel(event.response_status || "확인 필요")}</span></td><td><button className="report-icon-button" title={event.snapshot_url ? "사후 리포트 작성" : "캡처 없는 사건 확인"} aria-label={`${eventLabel(event.event_type)} 사후 리포트`} onClick={(click) => { click.stopPropagation(); onReport(event); }} onKeyDown={(key) => key.stopPropagation()}><FileText size={16}/><span>{event.snapshot_url ? "작성" : "캡처 없음"}</span></button></td></tr>)}</tbody></table></div>{filtered.length === 0 && <div className="empty-state"><p>조건에 맞는 이벤트가 없습니다.</p></div>}</section></div>;
}
export default History;
