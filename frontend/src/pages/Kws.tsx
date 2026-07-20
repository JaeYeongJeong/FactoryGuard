import { LoaderCircle, Mic, ShieldAlert, Volume2 } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { simulateKws } from "../api";
import type { DetectionEvent } from "../types";

function Kws({ onDetected }: { onDetected: (event: DetectionEvent) => void }) {
  const [text, setText] = useState("멈춰 위험해"); const [location, setLocation] = useState("제조 1라인");
  const [result, setResult] = useState<Record<string, any> | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const submit = async (submitEvent: FormEvent) => {
    submitEvent.preventDefault(); setLoading(true); setError(""); setResult(null);
    try { const data = await simulateKws({ text, location, equipment: "컨베이어", line_id: "line-1", force_stop: true }); setResult(data); if (data.backend_event) onDetected(data.backend_event); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "KWS 테스트에 실패했습니다."); }
    finally { setLoading(false); }
  };
  const detection = result?.detection;
  return <div><div className="page-heading"><div><h1>음성 긴급정지</h1><p className="page-desc">긴급 키워드를 감지해 즉시 설비 정지 명령과 이벤트 저장을 수행합니다.</p></div><span className="simulation-chip">SIMULATION</span></div><div className="tool-layout"><form className="panel tool-form" onSubmit={submit}><div className="kws-symbol"><Mic/></div><label>인식 문장<textarea rows={5} value={text} onChange={(change) => setText(change.target.value)} required/></label><label>발생 위치<input value={location} onChange={(change) => setLocation(change.target.value)}/></label>{error && <p className="error-text">{error}</p>}<button className="button danger full" disabled={loading}>{loading ? <><LoaderCircle className="spin"/>긴급정지 처리 중</> : <><Volume2/>긴급 발화 테스트</>}</button></form>
    <section className="panel result-panel"><h2>감지 및 제어 결과</h2>{!result ? <div className="empty-state"><Mic/><p>테스트 결과가 없습니다.</p></div> : <div className="kws-result"><div className={`detection-card ${detection?.detected ? "detected" : ""}`}><span>{detection?.detected ? "긴급 키워드 감지" : "키워드 미감지"}</span><strong>{detection?.keyword || "-"}</strong><b>{Math.round((detection?.confidence || 0) * 100)}%</b></div><dl className="event-details"><div><dt>언어</dt><dd>{detection?.language || "-"}</dd></div><div><dt>감지기</dt><dd>{detection?.detector || "-"}</dd></div><div><dt>백엔드 이벤트</dt><dd>{result.backend_saved ? "저장 완료" : "저장 실패"}</dd></div><div><dt>정지 명령</dt><dd>{result.stop_command?.accepted ? `${result.stop_command.mode} 승인` : "없음"}</dd></div></dl>{result.stop_command && <div className="stop-command"><ShieldAlert/><div><strong>{result.stop_command.command_id}</strong><small>{result.stop_command.reason}</small></div></div>}</div>}</section></div></div>;
}
export default Kws;
