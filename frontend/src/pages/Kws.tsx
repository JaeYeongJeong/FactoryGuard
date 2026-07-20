import { BookOpen, LoaderCircle, Mic, ShieldAlert, Volume2 } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { simulateKws } from "../api";
import type { DetectionEvent } from "../types";

function Kws({ onDetected }: { onDetected: (event: DetectionEvent) => void }) {
  const [text, setText] = useState("멈춰 위험해"); const [location, setLocation] = useState("제조 1라인"); const [rag, setRag] = useState(true);
  const [result, setResult] = useState<Record<string, any> | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const submit = async (submitEvent: FormEvent) => {
    submitEvent.preventDefault(); setLoading(true); setError(""); setResult(null);
    try { const data = await simulateKws({ text, location, equipment: "컨베이어", line_id: "line-1", force_stop: true, call_rag: rag }); setResult(data); if (data.backend_event) onDetected(data.backend_event); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "KWS 테스트에 실패했습니다."); }
    finally { setLoading(false); }
  };
  const detection = result?.detection; const ragReport = result?.rag_report;
  return <div><div className="page-heading"><div><h1>음성 긴급정지</h1><p className="page-desc">KWS 감지부터 설비 정지, 안전 근거 생성과 저장까지 확인합니다.</p></div><span className="simulation-chip">SIMULATION</span></div><div className="tool-layout"><form className="panel tool-form" onSubmit={submit}><div className="kws-symbol"><Mic/></div><label>인식 문장<textarea rows={5} value={text} onChange={(change) => setText(change.target.value)} required/></label><label>발생 위치<input value={location} onChange={(change) => setLocation(change.target.value)}/></label><label className="switch-row"><span><strong>RAG 안전 근거 생성</strong><small>긴급정지 이벤트에 관련 법령과 권장 조치를 연결</small></span><input type="checkbox" checked={rag} onChange={(change) => setRag(change.target.checked)}/></label>{error && <p className="error-text">{error}</p>}<button className="button danger full" disabled={loading}>{loading ? <><LoaderCircle className="spin"/>감지 및 RAG 처리 중</> : <><Volume2/>긴급 발화 테스트</>}</button></form>
    <section className="panel result-panel"><h2>감지 및 제어 결과</h2>{!result ? <div className="empty-state"><Mic/><p>테스트 결과가 없습니다.</p></div> : <div className="kws-result"><div className={`detection-card ${detection?.detected ? "detected" : ""}`}><span>{detection?.detected ? "긴급 키워드 감지" : "키워드 미감지"}</span><strong>{detection?.keyword || "-"}</strong><b>{Math.round((detection?.confidence || 0) * 100)}%</b></div><dl className="event-details"><div><dt>백엔드 이벤트</dt><dd>{result.backend_saved ? "저장 완료" : "저장 실패"}</dd></div><div><dt>정지 명령</dt><dd>{result.stop_command?.accepted ? `${result.stop_command.mode} 승인` : "없음"}</dd></div><div><dt>RAG 검색</dt><dd className={result.rag_used ? "success-text" : result.rag_error ? "danger-text" : ""}>{result.rag_used ? "적용 완료" : result.rag_error ? "실패" : "미사용"}</dd></div><div><dt>RAG 리포트</dt><dd>{result.report_backend_saved ? "저장 완료" : result.rag_used ? "저장 실패" : "미생성"}</dd></div></dl>{result.rag_error && <div className="rag-error"><ShieldAlert/><div><strong>RAG 처리 오류</strong><p>{result.rag_error}</p></div></div>}{ragReport && <div className="kws-rag-result"><h3><BookOpen size={17}/> RAG 권장 조치</h3><ul>{(ragReport.recommended_action || []).map((action: string) => <li key={action}>{action}</li>)}</ul><h3>검색 근거</h3>{(ragReport.legal_basis || []).map((basis: Record<string, any>, index: number) => <article key={index}><strong>{String(basis.title || "근거 자료")}</strong><small>{String(basis.source || basis.corpus || "")}</small></article>)}</div>}{result.stop_command && <div className="stop-command"><ShieldAlert/><div><strong>{result.stop_command.command_id}</strong><small>{result.stop_command.reason}</small></div></div>}</div>}</section></div></div>;
}
export default Kws;
