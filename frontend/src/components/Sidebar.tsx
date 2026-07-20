import { BarChart3, BookOpen, Camera, ClipboardList, FileSearch, Mic, ShieldAlert, X } from "lucide-react";

export type Page = "dashboard" | "monitoring" | "event" | "history" | "report" | "rag" | "kws";
type Props = { setPage: (page: Page) => void; currentPage: Page; streamStatus: string; open: boolean; close: () => void };
const items = [
  ["dashboard", "대시보드", BarChart3], ["monitoring", "CCTV 모니터링", Camera],
  ["event", "이벤트 응답", ShieldAlert], ["history", "감지 이력", ClipboardList],
  ["report", "AI 사후 리포트", FileSearch], ["rag", "안전 근거 검색", BookOpen], ["kws", "음성 긴급정지", Mic],
] as const;

function Sidebar({ setPage, currentPage, streamStatus, open, close }: Props) {
  return <>
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand"><div><h2>LineShield</h2><p>Conveyor Safety AI</p></div><button className="sidebar-close" onClick={close} aria-label="메뉴 닫기"><X /></button></div>
      <nav className="sidebar-menu">{items.map(([id, label, Icon]) => <button key={id} className={currentPage === id ? "active" : ""} onClick={() => setPage(id)}><Icon size={19}/><span>{label}</span></button>)}</nav>
      <div className="stream-state"><span className={`connection-dot ${streamStatus}`} /><div><strong>{streamStatus === "connected" ? "실시간 연결" : streamStatus === "connecting" ? "연결 중" : "연결 끊김"}</strong><small>백엔드 이벤트 스트림</small></div></div>
    </aside>
    {open && <button className="sidebar-backdrop" onClick={close} aria-label="메뉴 닫기" />}
  </>;
}
export default Sidebar;
