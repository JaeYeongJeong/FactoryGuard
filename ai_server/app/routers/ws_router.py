import json
import time
from collections import defaultdict
from typing import Dict, Set

import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["ws"])

# camera_id별 최신 프레임과 프론트 시청자 목록
latest_frames: Dict[str, bytes] = {}
viewers: Dict[str, Set[WebSocket]] = defaultdict(set)
camera_status: Dict[str, dict] = {}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "connected_cameras": list(camera_status.keys()),
        "viewer_counts": {k: len(v) for k, v in viewers.items()},
    }

@router.websocket("/cameras/{camera_id}")
async def camera_ingest(websocket: WebSocket, camera_id: str):
    """
    Camera Agent가 접속하는 엔드포인트.
    첫 메시지는 등록 JSON, 이후 메시지는 JPEG binary.
    """
    await websocket.accept()

    try:
        first_message = await websocket.receive_text()
        registration = json.loads(first_message)

        if registration.get("type") != "register":
            await websocket.close(code=1008, reason="register message required")
            return

        camera_status[camera_id] = {
            "location": registration.get("location", "unknown"),
            "connected_at": time.time(),
            "last_frame_at": None,
        }

        await websocket.send_json({
            "type": "registered",
            "camera_id": camera_id,
            "fps": 5,
        })

        while True:
            frame_bytes = await websocket.receive_bytes()

            # JPEG 디코딩
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # 데모용 분석 결과 표시.
            # 실제 프로젝트에서는 이 부분을 YOLO 추론 코드로 교체합니다.
            height, width = frame.shape[:2]
            cv2.rectangle(frame, (20, 20), (width - 20, height - 20), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"FactoryGuard | {camera_id}",
                (35, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                time.strftime("%Y-%m-%d %H:%M:%S"),
                (35, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            ok, encoded = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75]
            )
            if not ok:
                continue

            processed = encoded.tobytes()
            latest_frames[camera_id] = processed
            camera_status[camera_id]["last_frame_at"] = time.time()

            # 같은 카메라를 보고 있는 모든 프론트에 전달
            disconnected = []
            for viewer in list(viewers[camera_id]):
                try:
                    await viewer.send_bytes(processed)
                except Exception:
                    disconnected.append(viewer)

            for viewer in disconnected:
                viewers[camera_id].discard(viewer)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[camera:{camera_id}] error: {exc}")
    finally:
        camera_status.pop(camera_id, None)


@router.websocket("/view/{camera_id}")
async def camera_view(websocket: WebSocket, camera_id: str):
    """
    React/브라우저가 실시간 처리 영상을 받는 엔드포인트.
    """
    await websocket.accept()
    viewers[camera_id].add(websocket)

    try:
        # 연결 직후 최신 프레임이 있으면 즉시 전송
        if camera_id in latest_frames:
            await websocket.send_bytes(latest_frames[camera_id])

        # 연결 유지 및 종료 감지
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        viewers[camera_id].discard(websocket)