import { Check, LoaderCircle, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { eventLabel, severityLabel, statusLabel } from "../labels";
import type { DetectionEvent } from "../types";

function EventResponse({ events, saveResponse }: { events: DetectionEvent[]; saveResponse: (id: string, status: string, memo: string) => Promise<void> }) {
  const [selectedId, setSelectedId] = useState("");
  const selected = events.find((e) => e.event_id === selectedId) || events[0];
  const [memo, setMemo] = useState(""); const [saving, setSaving] = useState(false); const [message, setMessage] = useState("");
  useEffect(() => { setMemo(selected?.response_memo || ""); setMessage(""); }, [selected?.event_id, selected?.response_memo]);
  const save = async (status: string) => {
    if (!selected) return; setSaving(true); setMessage("");
    try { await saveResponse(selected.event_id, status, memo); setMessage("조치 내역을 저장했습니다."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "저장하지 못했습니다."); }
    finally { setSaving(false); }
  };
  if (!selected) return <div><h1>이벤트 응답</h1><section className="panel empty-state"><Check/><p>응답할 이벤트가 없습니다.</p></section></div>;
  return <div><div className="page-heading"><div><h1>이벤트 응답</h1><p className="page-desc">위험 이벤트를 확인하고 현장 조치를 기록합니다.</p></div><select value={selected.event_id} onChange={(e) => setSelectedId(e.target.value)}>{events.map((e) => <option value={e.event_id} key={e.event_id}>{eventLabel(e.event_type)} · {e.zone_name}</option>)}</select></div>
    <section className="response-layout"><div className="panel"><div className="panel-header"><h2><ShieldAlert size={20}/> 감지 상세</h2><span className={`badge ${selected.severity}`}>{severityLabel(selected.severity)}</span></div>{selected.snapshot_url && <img className="event-snapshot" src={selected.snapshot_url} alt="위험 감지 캡처"/>}<dl className="event-details"><div><dt>발생 시각</dt><dd>{new Date(selected.timestamp).toLocaleString("ko-KR")}</dd></div><div><dt>위험 유형</dt><dd>{eventLabel(selected.event_type)}</dd></div><div><dt>위치</dt><dd>{selected.zone_name} ({selected.camera_id})</dd></div><div><dt>작업자</dt><dd>#{selected.worker_id}</dd></div><div><dt>현재 상태</dt><dd>{statusLabel(selected.status)}</dd></div></dl><p className="event-message">{selected.message}</p></div>
      <div className="panel response-form"><h2>관리자 조치</h2><textarea className="memo" value={memo} onChange={(e) => setMemo(e.target.value)} placeholder="현장 확인 결과와 조치 내용을 입력하세요."/><div className="response-actions"><button onClick={() => void save("stopped")} className="button danger" disabled={saving}>작업중지</button><button onClick={() => void save("checking")} className="button secondary" disabled={saving}>현장 확인 중</button><button onClick={() => void save("resolved")} className="button" disabled={saving}>조치 완료</button><button onClick={() => void save("false_positive")} className="button ghost" disabled={saving}>오탐 처리</button></div>{saving && <p><LoaderCircle className="spin" size={16}/> 저장 중</p>}{message && <p className="form-message">{message}</p>}</div>
    </section>
  </div>;
}
export default EventResponse;
