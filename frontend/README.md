# LineShield Frontend

FactoryGuard 백엔드 및 AI 서버와 연결되는 React/Vite 관제 화면입니다.

## 실행

```bash
npm install
cp .env.example .env
npm run dev
```

기본 주소는 백엔드 `http://localhost:8000`, AI 서버 `http://localhost:8001`입니다.
배포 환경에서는 `.env`의 `VITE_API_BACKEND_URL`, `VITE_API_AI_URL`,
`VITE_EVENT_WS_URL`, `VITE_AI_WS_URL`을 공개 주소로 변경하세요. HTTPS 페이지에서는
WebSocket 주소도 반드시 `wss://`를 사용해야 합니다.

## 주요 연결

- 위험 이벤트: `GET /events`, `WS /events/stream`
- 이벤트 조치: `PATCH /events/{event_id}`
- AI 영상: AI 서버 `WS /ws/view/{camera_id}`
- 감지 사건 사후 분석: `POST /reports/analyze-event/{event_id}`
- RAG: `POST /rag/search`
- KWS: `POST /kws/simulate`
