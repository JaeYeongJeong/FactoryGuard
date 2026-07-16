import asyncio
import json
import time
from collections import defaultdict
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.services.frame_service import FrameService


class WebSocketService:
    """카메라 및 프론트엔드 WebSocket 연결을 관리합니다."""

    def __init__(self, frame_service: Optional[FrameService] = None) -> None:
        self.latest_frames: Dict[str, bytes] = {}
        self.viewers = defaultdict(set)
        self.camera_status: Dict[str, dict] = {}
        self.frame_service = frame_service

    def configure(self, frame_service: FrameService) -> None:
        """애플리케이션 시작 시 조립된 프레임 서비스를 연결합니다."""
        self.frame_service = frame_service

    def get_health(self) -> dict:
        """현재 카메라 및 시청자 연결 상태를 반환합니다."""
        return {
            "status": "ok",
            "connected_cameras": list(self.camera_status.keys()),
            "viewer_counts": {
                camera_id: len(camera_viewers)
                for camera_id, camera_viewers in self.viewers.items()
            },
            "frame_service_ready": self.frame_service is not None,
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

        self.camera_status[camera_id] = {
            "location": registration.get(
                "location",
                "unknown",
            ),
            "connected_at": time.time(),
            "last_frame_at": None,
            "processed_frames": 0,
            "detected_events": 0,
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

            if self.frame_service is None:
                await websocket.close(
                    code=1011,
                    reason="vision pipeline is not ready",
                )
                return

            while True:
                frame_bytes = await websocket.receive_bytes()

                processed_frame, events = await asyncio.to_thread(
                    self.frame_service.process_frame,
                    frame_bytes=frame_bytes,
                    camera_id=camera_id,
                )

                if processed_frame is None:
                    continue

                self.latest_frames[camera_id] = processed_frame
                self.camera_status[camera_id]["last_frame_at"] = time.time()
                self.camera_status[camera_id]["processed_frames"] += 1
                self.camera_status[camera_id]["detected_events"] += len(events)

                await self.broadcast_frame(
                    camera_id=camera_id,
                    frame_bytes=processed_frame,
                )

        except WebSocketDisconnect:
            logger.info(f"카메라 WebSocket 연결 종료: {camera_id}")

        except Exception as exc:
            logger.exception(f"카메라 WebSocket 처리 오류 ({camera_id}): {exc}")

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
            logger.info(f"Viewer WebSocket 연결 종료: {camera_id}")

        except Exception as exc:
            logger.warning(f"Viewer WebSocket 처리 오류 ({camera_id}): {exc}")

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
