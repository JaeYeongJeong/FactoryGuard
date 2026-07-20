import { useEffect, useRef, useState } from "react";
import { EVENT_WS_URL } from "../api";
import type { DetectionEvent } from "../types";

export function useEventStream(onEvent: (event: DetectionEvent) => void) {
  const callback = useRef(onEvent);
  const [status, setStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  useEffect(() => { callback.current = onEvent; }, [onEvent]);
  useEffect(() => {
    let socket: WebSocket | null = null;
    let timer = 0;
    let stopped = false;
    let retry = 0;
    const connect = () => {
      setStatus("connecting");
      socket = new WebSocket(`${EVENT_WS_URL}/events/stream`);
      socket.onopen = () => { retry = 0; setStatus("connected"); };
      socket.onmessage = ({ data }) => {
        try { callback.current(JSON.parse(data) as DetectionEvent); } catch { /* keep stream alive */ }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        setStatus("disconnected");
        if (!stopped) timer = window.setTimeout(connect, Math.min(1000 * 2 ** retry++, 15000));
      };
    };
    connect();
    return () => { stopped = true; window.clearTimeout(timer); socket?.close(); };
  }, []);
  return status;
}
