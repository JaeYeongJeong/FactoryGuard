# FactoryGuard
python 3.10
conda 환경
conda env list
conda activate [콘다명]

### 백엔드 서버 실행 명령어
cd FactoryGuard/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

### ai 서버 실행 명령어
cd FactoryGuard/ai_server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

### cloudflared tunnel 실행 명령어
cloudflared tunnel run factoryguard-api

프로젝트 루트의 `.env`는 실행 위치와 관계없이 AI 서버와 백엔드 서버가 함께 읽습니다.
내부 서비스 통신에는 `API_BACKEND_URL`, 외부 공개 주소에는
`API_BACKEND_PUBLIC_URL`, `API_AI_PUBLIC_URL`, `API_CAPTURE_BASE_URL`을 사용합니다.

### Vision LLM / RAG / KWS 엔드포인트

- `POST /reports/analyze`: 이미지 Vision LLM 분석 및 백엔드 보고서 저장
- `POST /reports/analyze-with-legal-basis`: Vision 분석, RAG 근거 결합, 백엔드 저장
- `POST /rag/search`: 이벤트 기반 안전·개인정보 근거 검색
- `POST /rag/report`: 근거, 권장조치, LLM 컨텍스트 생성
- `POST /kws/simulate`: 긴급 키워드 시뮬레이션, 백엔드 이벤트 저장
- `POST /kws/stop-test`: `dry_run` 정지 경로 점검

RAG는 `ai_server/data/rag_indexes`의 FAISS 인덱스를 사용하며 임베딩 모델은
첫 RAG 요청 시 로드됩니다. KWS는 현재 팀원 구현과 동일하게 텍스트 시뮬레이션
단계이며, 실제 마이크 모델 연동 전까지 액추에이터는 `dry_run`만 허용합니다.

# Project Structure

```text
FactoryGuard
│
├── ai_server/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── vision_ai/
│   │   │   └── vision_llm/
│   │   └── services/
│   │       ├── vision_ai/
│   │       │   ├── communication/
│   │       │   ├── core/
│   │       │   ├── processing/
│   │       │   ├── utils/
│   │       │   └── visualization/
│   │       └── vision_llm/
│   │
│   ├── captures/
│   ├── data/
│   └── vector_db/
│
├── backend_server/
│   └── app/
│       ├── config.py
│       ├── main.py
│       ├── db/
│       └── routers/
├── .env
├── environment.yml
└── README.md
```

---

# Directory Description

## ai_server/

Vision AI 모델이 실행되는 서버입니다.

카메라로부터 영상을 수신하고 AI 추론을 수행한 뒤, 결과를 프론트엔드 및 백엔드로 전달합니다.

### app/

AI 서버의 핵심 애플리케이션입니다.

#### config.py

AI 서버에서 사용하는 환경변수 및 설정을 관리합니다.

* OpenAI API Key
* 기타 서버 설정

---

#### main.py

FastAPI 애플리케이션을 생성합니다.

* Router 등록
* 서버 초기화
* Health Check API 제공

---

### routers/

클라이언트와 통신하는 API(WebSocket / HTTP)를 정의합니다.

라우터에서는 요청을 받아 필요한 Service를 호출하고 결과를 반환하는 역할만 수행합니다.

#### vision_ai/ws_router.py

WebSocket 기반 영상 스트리밍 API입니다.

주요 기능

* Camera Agent 연결
* Browser Viewer 연결
* 실시간 영상 송수신

#### vision_llm/reports_router.py

Vision LLM 사고 분석 API입니다.

주요 기능

* 사고 이미지 업로드
* 사고 분석 요청
* 보고서 반환

---

### services/

AI 서버의 실제 비즈니스 로직을 담당합니다.

#### vision_ai/websocket_service.py

WebSocket 연결을 관리합니다.

주요 기능

* Camera 등록
* Viewer 등록
* 연결 상태 관리
* 실시간 프레임 Broadcast

---

#### vision_ai/frame_service.py

영상 프레임을 처리합니다.

주요 기능

* JPEG Decode
* OpenCV 전처리
* YOLO 객체 탐지
* Bounding Box 생성
* JPEG Encode

---

#### vision_llm/accident_report_service.py

Vision LLM(OpenAI)을 이용한 사고 분석 서비스입니다.

주요 기능

* 이미지 Base64 변환
* GPT Vision 호출
* 사고 보고서 생성

---

### captures/

위험 상태가 처음 감지된 프레임을 JPEG로 저장합니다.

기본 저장 조건은 `entered` 이벤트이며, 저장 위치는 `EVENT_SNAPSHOT_DIR` 환경변수로 변경할 수 있습니다.

---

### 위험 이벤트 연동

Vision AI는 위험 이벤트를 백엔드 `POST /events/detect`로 전송합니다. 백엔드는 MongoDB 저장 후 프론트엔드 WebSocket `WS /events/stream`으로 동일한 이벤트를 전송합니다.

프론트엔드는 `GET /events?limit=50`으로 최근 이벤트를 조회할 수 있습니다.
파일명을 제외한 공개 캡처 주소는 `API_CAPTURE_BASE_URL`에 설정합니다.
예를 들어 `API_CAPTURE_BASE_URL=https://ai.j-jandy.com/captures`로 설정하면
DB에는 `https://ai.j-jandy.com/captures/{파일명}` 형태로 저장됩니다.
`API_CAPTURE_BASE_URL`이 없으면 기존처럼 `API_AI_PUBLIC_URL/captures`를 사용합니다.

```json
{
  "event_id": "4c9bde23-5b41-46f0-b998-4ab836ad77b9",
  "camera_id": "cam-01",
  "timestamp": "2026-07-16T04:30:00+00:00",
  "event_type": "intrusion",
  "severity": "critical",
  "status": "entered",
  "worker_id": 12,
  "zone_name": "프레스 위험구역",
  "message": "작업자 12의 위험구역 프레스 위험구역 침입이 감지되었습니다.",
  "snapshot_url": "http://localhost:8001/captures/example.jpg"
}
```

---

### data/

테스트용 이미지 데이터가 저장됩니다.

예시

* 사고 이미지
* 테스트 이미지

---

### vector_db/

향후 RAG(Retrieval-Augmented Generation)를 위한 Vector Database 저장 위치입니다.

산업안전 매뉴얼, 사고 대응 문서 등을 저장하여 Vision LLM과 함께 사용할 예정입니다.

---

# backend_server/

AI 서버에서 전달받은 이벤트를 관리하는 서버입니다.

MongoDB와 연동하여 이벤트 및 사고 정보를 저장하고 조회합니다.

---

## app/

백엔드 서버의 핵심 애플리케이션입니다.

### config.py

백엔드 환경설정을 관리합니다.

* MongoDB URI
* 기타 서버 설정

---

### main.py

FastAPI 애플리케이션을 생성합니다.

* Router 등록
* MongoDB 초기화
* Health Check API 제공

---

### db/

MongoDB 관련 모듈입니다.

#### mongodb.py

MongoDB 연결을 생성합니다.

#### collections.py

컬렉션 생성 및 인덱스를 관리합니다.

예시

* events
* reports
* camera_captures

---

### routers/

REST API를 제공합니다.

#### events_router.py

이벤트 조회 및 관리 API

예시

* 이벤트 목록 조회
* 이벤트 상세 조회

#### reports_router.py

사고 보고서 조회 API

예시

* 사고 보고서 조회
* 사고 보고서 관리

---

# environment.yml

Conda 실행 환경을 정의합니다.

포함 내용

* Python 버전
* 필수 라이브러리
* 실행 환경 설정

---

# README.md

프로젝트 설명 및 실행 방법을 제공합니다.
