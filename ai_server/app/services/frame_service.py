import time

import cv2
import numpy as np


class FrameService:
    """카메라 프레임 디코딩, 분석, 인코딩을 담당합니다."""

    @staticmethod
    def decode_frame(frame_bytes: bytes) -> np.ndarray | None:
        """JPEG 바이너리를 OpenCV 이미지로 변환합니다."""
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        return cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    @staticmethod
    def analyze_frame(frame: np.ndarray, camera_id: str) -> np.ndarray:
        """
        프레임 분석 결과를 이미지에 표시합니다.

        현재는 데모용 박스와 텍스트만 출력합니다.
        이후 이 메서드 내부를 YOLO 추론 코드로 교체하면 됩니다.
        """
        height, width = frame.shape[:2]

        cv2.rectangle(
            frame,
            (20, 20),
            (width - 20, height - 20),
            (0, 255, 0),
            2,
        )

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

        return frame

    @staticmethod
    def encode_frame(frame: np.ndarray, quality: int = 75) -> bytes | None:
        """OpenCV 이미지를 JPEG 바이너리로 변환합니다."""
        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality],
        )

        if not success:
            return None

        return encoded.tobytes()

    def process_frame(
        self,
        frame_bytes: bytes,
        camera_id: str,
    ) -> bytes | None:
        """프레임 디코딩부터 분석, 재인코딩까지 수행합니다."""
        frame = self.decode_frame(frame_bytes)

        if frame is None:
            return None

        analyzed_frame = self.analyze_frame(frame, camera_id)

        return self.encode_frame(analyzed_frame)