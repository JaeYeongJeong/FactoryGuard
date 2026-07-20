import { ArrowLeft, BookOpen, FileImage, LoaderCircle, Printer } from "lucide-react";
import { useEffect, useState } from "react";
import { analyzeEvent } from "../api";
import { eventLabel, severityLabel, statusLabel } from "../labels";
import type { DetectionEvent, IncidentReport } from "../types";

type Props = {
  event: DetectionEvent | null;
  events: DetectionEvent[];
  reports: IncidentReport[];
  onSelectEvent: (event: DetectionEvent | null) => void;
  onCreated: () => Promise<void>;
  onOpenHistory: () => void;
};

function Report({ event, events, reports, onSelectEvent, onCreated, onOpenHistory }: Props) {
  const linkedReport = reports.find((report) => report.event_id === event?.event_id) || null;
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [selected, setSelected] = useState<IncidentReport | null>(linkedReport);
  const [loading, setLoading] = useState(false); const [error, setError] = useState("");

  useEffect(() => {
    setResult(null); setError("");
    setSelected(reports.find((report) => report.event_id === event?.event_id) || null);
  }, [event?.event_id, reports]);

  const chooseEvent = (eventId: string) => onSelectEvent(events.find((item) => item.event_id === eventId) || null);
  const submit = async () => {
    if (!event?.snapshot_url) return;
    setLoading(true); setError("");
    try { setResult(await analyzeEvent(event.event_id)); await onCreated(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "분석에 실패했습니다."); }
    finally { setLoading(false); }
  };
  const visible = result || selected;

  return <div><div className="page-heading report-head"><div><h1>AI 사후 리포트</h1><p className="page-desc">감지 이력을 선택하고 저장된 캡처로 사고 상황과 안전 근거를 분석합니다.</p></div><button className="button secondary" onClick={() => window.print()} disabled={!visible}><Printer size={17}/> 인쇄</button></div>
    <div className="report-workspace"><section className="panel report-builder"><div className="report-event-picker"><label>감지 이력 선택<select value={event?.event_id || ""} onChange={(change) => chooseEvent(change.target.value)}><option value="">분석할 사건을 선택하세요</option>{events.map((item) => <option value={item.event_id} key={item.event_id}>{new Date(item.timestamp).toLocaleString("ko-KR")} · {eventLabel(item.event_type)} · {item.zone_name}{item.snapshot_url ? "" : " (캡처 없음)"}</option>)}</select></label><button className="back-link" onClick={onOpenHistory}><ArrowLeft size={16}/> 전체 감지 이력 보기</button></div>{!event ? <div className="empty-state compact"><FileImage/><p>위 목록에서 분석할 감지 사건을 선택하세요.</p></div> : <><div className="selected-incident"><div><small>{new Date(event.timestamp).toLocaleString("ko-KR")}</small><h2>{eventLabel(event.event_type)}</h2><p>{event.zone_name} · 작업자 #{event.worker_id}</p></div><span className={`badge ${event.severity}`}>{severityLabel(event.severity)}</span></div>{event.snapshot_url ? <img className="report-capture" src={event.snapshot_url} alt={`${eventLabel(event.event_type)} 감지 캡처`}/> : <div className="capture-missing"><FileImage/><strong>저장된 캡처가 없습니다.</strong><small>최초 감지 시 캡처 저장 설정을 확인하세요.</small></div>}<dl className="event-details"><div><dt>감지 상태</dt><dd>{statusLabel(event.status)}</dd></div><div><dt>조치 상태</dt><dd>{statusLabel(event.response_status || "확인 필요")}</dd></div><div><dt>지속 시간</dt><dd>{Math.round(event.duration || 0)}초</dd></div></dl>{error && <p className="error-text">{error}</p>}<button className="button full" disabled={!event.snapshot_url || loading} onClick={() => void submit()}>{loading ? <><LoaderCircle className="spin"/>분석 중</> : <><FileImage/>사후 리포트 작성</>}</button></>}</section>
      <section className="panel report-document">{!visible ? <div className="empty-state"><FileImage/><p>{event ? "선택된 사건의 리포트를 작성하세요." : "감지 사건을 선택하세요."}</p></div> : <><div className="report-title"><div><small>{String(visible.source || "VISION LLM")}</small><h2>산업 안전 사고 분석 보고서</h2></div><span>{String(visible.report_id || "새 분석")}</span></div>{event?.snapshot_url && <figure className="report-evidence-image"><img src={event.snapshot_url} alt={`${eventLabel(event.event_type)} 리포트 증빙 이미지`}/><figcaption>{event.zone_name} · {new Date(event.timestamp).toLocaleString("ko-KR")}</figcaption></figure>}<div className="report-body">{String(visible.report || "")}</div>{Array.isArray(visible.recommended_action) && visible.recommended_action.length > 0 && <div className="report-section"><h3>권장 조치</h3><ol>{visible.recommended_action.map((action: string) => <li key={action}>{action}</li>)}</ol></div>}{Array.isArray(visible.legal_basis) && visible.legal_basis.length > 0 && <div className="report-section"><h3><BookOpen size={18}/> 법령 및 안전 근거</h3>{visible.legal_basis.map((basis: Record<string, any>, index: number) => <article className="legal-item" key={index}><strong>{String(basis.title || basis.section || "근거 자료")}</strong><small>{String(basis.source || basis.corpus || "")}{basis.pages ? ` · ${basis.pages}쪽` : ""}</small><p>{String(basis.reason || basis.text || "")}</p></article>)}</div>}</>}</section></div>
  </div>;
}
export default Report;
