import { Archive, BookOpen, FileImage, Printer } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { eventLabel } from "../labels";
import type { DetectionEvent, IncidentReport } from "../types";

function SavedReports({ reports, events }: { reports: IncidentReport[]; events: DetectionEvent[] }) {
  const [selectedId, setSelectedId] = useState(reports[0]?.report_id || "");
  useEffect(() => { if (!selectedId && reports[0]) setSelectedId(reports[0].report_id); }, [reports, selectedId]);
  const selected = reports.find((report) => report.report_id === selectedId) || reports[0] || null;
  const linkedEvent = useMemo(() => events.find((event) => event.event_id === selected?.event_id) || null, [events, selected?.event_id]);

  return <div><div className="page-heading report-head"><div><h1>저장된 리포트</h1><p className="page-desc">Vision LLM과 KWS RAG가 생성해 저장한 리포트를 확인합니다.</p></div><button className="button secondary" onClick={() => window.print()} disabled={!selected}><Printer size={17}/> 인쇄</button></div>
    <div className="archive-layout"><section className="panel report-archive"><div className="panel-header"><h2><Archive size={18}/> 리포트 목록</h2><span>{reports.length}건</span></div>{reports.length === 0 ? <div className="empty-state compact"><Archive/><p>저장된 리포트가 없습니다.</p></div> : reports.map((report) => <button className={selected?.report_id === report.report_id ? "active" : ""} key={report.report_id} onClick={() => setSelectedId(report.report_id)}><div><strong>{linkedLabel(report, events)}</strong><small>{new Date(report.created_at).toLocaleString("ko-KR")}</small></div><span>{sourceLabel(report.source)}</span></button>)}</section>
      <section className="panel report-document">{!selected ? <div className="empty-state"><FileImage/><p>확인할 리포트를 선택하세요.</p></div> : <><div className="report-title"><div><small>{sourceLabel(selected.source)}</small><h2>산업 안전 사고 분석 보고서</h2></div><span>{selected.report_id}</span></div>{linkedEvent?.snapshot_url && <figure className="report-evidence-image"><img src={linkedEvent.snapshot_url} alt={`${eventLabel(linkedEvent.event_type)} 감지 캡처`}/><figcaption>{linkedEvent.zone_name} · {new Date(linkedEvent.timestamp).toLocaleString("ko-KR")}</figcaption></figure>}<div className="report-body">{selected.report}</div>{selected.recommended_action.length > 0 && <div className="report-section"><h3>권장 조치</h3><ol>{selected.recommended_action.map((action) => <li key={action}>{action}</li>)}</ol></div>}{selected.legal_basis.length > 0 && <div className="report-section"><h3><BookOpen size={18}/> 법령 및 안전 근거</h3>{selected.legal_basis.map((basis, index) => <article className="legal-item" key={index}><strong>{String(basis.title || "근거 자료")}</strong><small>{String(basis.source || basis.corpus || "")}{basis.pages ? ` · ${basis.pages}쪽` : ""}</small><p>{String(basis.reason || "")}</p></article>)}</div>}</>}</section></div>
  </div>;
}

function sourceLabel(source: string) { return source === "kws_rag" ? "KWS + RAG" : source === "vision_llm_rag" ? "Vision LLM + RAG" : source; }
function linkedLabel(report: IncidentReport, events: DetectionEvent[]) { const event = events.find((item) => item.event_id === report.event_id); return event ? `${eventLabel(event.event_type)} · ${event.zone_name}` : report.event_id || "연결 사건 없음"; }
export default SavedReports;
