import { Camera, CircleStop, LoaderCircle, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AI_WS_URL } from "../api";

function Monitoring() {
  const [cameraId, setCameraId] = useState("cam-01");
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState("CCTV 연결 대기 중");
  const [frame, setFrame] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const urlRef = useRef<string | null>(null);

  const disconnect = () => {
    socketRef.current?.close(); socketRef.current = null;
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    urlRef.current = null; setFrame(null); setConnected(false); setStatus("CCTV 연결 대기 중");
  };
  useEffect(() => disconnect, []);
  const connect = () => {
    if (socketRef.current) return;
    setStatus("AI 영상 서버에 연결 중");
    const socket = new WebSocket(`${AI_WS_URL}/ws/view/${encodeURIComponent(cameraId)}`);
    socket.binaryType = "blob";
    socket.onopen = () => { setConnected(true); setStatus("처리 영상 수신 대기 중"); };
    socket.onmessage = ({ data }) => {
      if (!(data instanceof Blob)) return;
      const next = URL.createObjectURL(data); if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = next; setFrame(next); setStatus("AI 처리 영상 수신 중");
    };
    socket.onerror = () => { setStatus("영상 서버 연결에 실패했습니다."); socket.close(); };
    socket.onclose = () => { socketRef.current = null; setConnected(false); };
    socketRef.current = socket;
  };
  return <div><div className="page-heading"><div><h1>실시간 CCTV 모니터링</h1><p className="page-desc">AI 서버에서 분석한 카메라 프레임을 확인합니다.</p></div></div>
    <section className="panel"><div className="panel-header monitoring-tools"><div><h2>카메라 영상</h2><span>{status}</span></div><div className="camera-controls"><label>카메라 ID<input value={cameraId} onChange={(e) => setCameraId(e.target.value)} disabled={connected}/></label><button className={connected ? "button danger" : "button"} onClick={connected ? disconnect : connect}>{connected ? <><CircleStop size={17}/>연결 종료</> : <><Play size={17}/>연결</>}</button></div></div>
      <div className="camera-area">{frame ? <img src={frame} className="camera-frame" alt={`${cameraId} 실시간 분석 영상`}/> : <div className="camera-placeholder">{connected ? <LoaderCircle className="spin" size={38}/> : <Camera size={42}/>}<strong>{status}</strong><small>카메라 에이전트가 같은 ID로 연결되어 있어야 합니다.</small></div>}</div>
    </section>
  </div>;
}
export default Monitoring;
