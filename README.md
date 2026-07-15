# FactoryGuard
python 3.10
conda 환경
conda env list
conda activate [콘다명]

### 백엔드 서버 실행 명령어
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

### ai 서버 실행 명령어
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

### cloudflared tunnel 실행 명령어
cloudflared tunnel run factoryguard-api

# Project Structure

```text
FactoryGuard
│
├── ai_server/
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── routers/
│   │   └── services/
│   │
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

#### ws_router.py

WebSocket 기반 영상 스트리밍 API입니다.

주요 기능

* Camera Agent 연결
* Browser Viewer 연결
* 실시간 영상 송수신

#### reports_router.py

Vision LLM 사고 분석 API입니다.

주요 기능

* 사고 이미지 업로드
* 사고 분석 요청
* 보고서 반환

---

### services/

AI 서버의 실제 비즈니스 로직을 담당합니다.

#### websocket_service.py

WebSocket 연결을 관리합니다.

주요 기능

* Camera 등록
* Viewer 등록
* 연결 상태 관리
* 실시간 프레임 Broadcast

---

#### frame_service.py

영상 프레임을 처리합니다.

주요 기능

* JPEG Decode
* OpenCV 전처리
* YOLO 객체 탐지
* Bounding Box 생성
* JPEG Encode

---

#### accident_report_service.py

Vision LLM(OpenAI)을 이용한 사고 분석 서비스입니다.

주요 기능

* 이미지 Base64 변환
* GPT Vision 호출
* 사고 보고서 생성

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
