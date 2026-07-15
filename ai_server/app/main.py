from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers.ws_router import router as ws_router

app = FastAPI(title="FactoryGuard Vision Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 데모용. 운영에서는 프론트 도메인만 허용하세요.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ai server ok"}

# 테스트용
@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse("""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FactoryGuard Camera Demo</title>
  <style>
    body { font-family: sans-serif; max-width: 1000px; margin: 30px auto; padding: 0 16px; }
    .toolbar { display:flex; gap:8px; margin-bottom:16px; }
    input, button { padding:10px; font-size:16px; }
    img { width:100%; max-width:900px; background:#111; border-radius:12px; }
    #status { margin:12px 0; font-weight:700; }
  </style>
</head>
<body>
  <h1>공장수호대 실시간 카메라 데모</h1>
  <div class="toolbar">
    <input id="cameraId" value="cam-01" />
    <button onclick="connectStream()">연결</button>
    <button onclick="disconnectStream()">해제</button>
  </div>
  <div id="status">대기 중</div>
  <img id="video" alt="실시간 영상" />

<script>
let ws = null;
let previousUrl = null;

function connectStream() {
  disconnectStream();

  const cameraId = document.getElementById("cameraId").value.trim();
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${scheme}://${location.host}/ws/view/${cameraId}`);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    document.getElementById("status").textContent = `${cameraId} 연결됨`;
  };

  ws.onmessage = (event) => {
    const blob = new Blob([event.data], { type: "image/jpeg" });
    const url = URL.createObjectURL(blob);
    document.getElementById("video").src = url;

    if (previousUrl) URL.revokeObjectURL(previousUrl);
    previousUrl = url;
  };

  ws.onclose = () => {
    document.getElementById("status").textContent = "연결 종료";
  };

  ws.onerror = () => {
    document.getElementById("status").textContent = "연결 오류";
  };
}

function disconnectStream() {
  if (ws) {
    ws.close();
    ws = null;
  }
}
</script>
</body>
</html>
""")


