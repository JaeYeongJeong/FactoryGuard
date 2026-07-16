import logging

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


class EventSenderService:
    def __init__(self) -> None:
        self.backend_url = settings.api.backend_url.rstrip("/")

    async def send_event(self, event_data: dict) -> bool:
        """
        감지 이벤트를 백엔드 서버로 전송합니다.
        """
        endpoint = f"{self.backend_url}/events/detect"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    endpoint,
                    json=event_data,
                )

                response.raise_for_status()

                return True

        except httpx.TimeoutException:
            logger.error(
                "백엔드 이벤트 전송 시간 초과: %s",
                endpoint,
            )
            return False

        except httpx.HTTPStatusError as exc:
            logger.error(
                "백엔드 이벤트 전송 실패: status=%s, body=%s",
                exc.response.status_code,
                exc.response.text,
            )
            return False

        except httpx.HTTPError as exc:
            logger.error(
                "백엔드 연결 실패: %s",
                exc,
            )
            return False


event_sender_service = EventSenderService()
