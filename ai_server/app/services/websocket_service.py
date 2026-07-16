import json
import time
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.services.frame_service import FrameService


class WebSocketService:
    """카메라 및 프론트엔드 WebSocket 연결을 관리합니다."""

    def __init__(self) -> None:
        self.latest_frames: Dict[str, bytes] = {}
        self.viewers = defaultdict(set)
        self.camera_status: Dict[str, dict] = {}

        self.video_sources: Dict[
            str,
            WebSocketVideoSource,
        ] = {}

    def get_health(self) -> dict:
        """현재 카메라 및 시청자 연결 상태를 반환합니다."""
        return {
            "status": "ok",
            "connected_cameras": list(self.camera_status.keys()),
            "viewer_counts": {
                camera_id: len(camera_viewers)
                for camera_id, camera_viewers in self.viewers.items()
            },
        }

    async def register_camera(
        self,
        websocket: WebSocket,
        camera_id: str,
    ) -> bool:
        first_message = await websocket.receive_text()

        try:
            registration = json.loads(first_message)
        except json.JSONDecodeError:
            await websocket.close(
                code=1008,
                reason="invalid registration json",
            )
            return False

        if registration.get("type") != "register":
            await websocket.close(
                code=1008,
                reason="register message required",
            )
            return False

        source = WebSocketVideoSource(
            camera_id=camera_id,
            resize=(1280, 720),
            fps=5.0,
        )

        source.open()

        self.video_sources[camera_id] = source

        self.camera_status[camera_id] = {
            "location": registration.get(
                "location",
                "unknown",
            ),
            "connected_at": time.time(),
            "last_frame_at": None,
        }

        await websocket.send_json(
            {
                "type": "registered",
                "camera_id": camera_id,
                "fps": 5,
            }
        )

        return True

    async def handle_camera(
        self,
        websocket: WebSocket,
        camera_id: str,
    ) -> None:
        """Camera Agent 연결과 프레임 수신을 처리합니다."""
        await websocket.accept()

        try:
            registered = await self.register_camera(
                websocket=websocket,
                camera_id=camera_id,
            )

            if not registered:
                return

            while True:
                frame_bytes = await websocket.receive_bytes()

                frame_array = np.frombuffer(
                    frame_bytes,
                    dtype=np.uint8,
                )

                frame = cv2.imdecode(
                    frame_array,
                    cv2.IMREAD_COLOR,
                )

                if frame is None:
                    continue

                processed_frame, events = self.frame_service.process_frame(
                    frame=frame,
                    camera_id=camera_id,
                )

                if processed_frame is None:
                    continue

                self.latest_frames[camera_id] = processed_frame
                self.camera_status[camera_id]["last_frame_at"] = time.time()

                await self.broadcast_frame(
                    camera_id=camera_id,
                    frame_bytes=processed_frame,
                )

        except WebSocketDisconnect:
            print(f"[camera:{camera_id}] disconnected")

        except Exception as exc:
            print(f"[camera:{camera_id}] error: {exc}")

        finally:
            self.disconnect_camera(camera_id)

    async def handle_viewer(
        self,
        websocket: WebSocket,
        camera_id: str,
    ) -> None:
        """프론트엔드 영상 시청자 연결을 처리합니다."""
        await websocket.accept()
        self.viewers[camera_id].add(websocket)

        try:
            latest_frame = self.latest_frames.get(camera_id)

            if latest_frame is not None:
                await websocket.send_bytes(latest_frame)

            while True:
                # 클라이언트 연결 종료를 감지하기 위한 대기
                await websocket.receive()

        except WebSocketDisconnect:
            print(f"[viewer:{camera_id}] disconnected")

        except Exception as exc:
            print(f"[viewer:{camera_id}] error: {exc}")

        finally:
            self.disconnect_viewer(
                camera_id=camera_id,
                websocket=websocket,
            )

    async def broadcast_frame(
        self,
        camera_id: str,
        frame_bytes: bytes,
    ) -> None:
        """같은 카메라를 보고 있는 모든 시청자에게 프레임을 전송합니다."""
        disconnected_viewers: list[WebSocket] = []

        for viewer in list(self.viewers[camera_id]):
            try:
                await viewer.send_bytes(frame_bytes)
            except Exception:
                disconnected_viewers.append(viewer)

        for viewer in disconnected_viewers:
            self.viewers[camera_id].discard(viewer)

    def disconnect_camera(self, camera_id: str) -> None:
        """카메라 연결 정보를 제거합니다."""
        self.camera_status.pop(camera_id, None)

    def disconnect_viewer(
        self,
        camera_id: str,
        websocket: WebSocket,
    ) -> None:
        """시청자 연결 정보를 제거합니다."""
        self.viewers[camera_id].discard(websocket)

        if not self.viewers[camera_id]:
            self.viewers.pop(camera_id, None)


websocket_service = WebSocketService()