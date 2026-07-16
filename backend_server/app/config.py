import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_SERVER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 실제 환경변수를 우선하며 서비스별 파일과 프로젝트 공용 파일을 보완합니다.
load_dotenv(BACKEND_SERVER_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI 환경변수가 설정되지 않았습니다.")
  
