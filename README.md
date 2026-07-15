# FactoryGuard
python 3.10
conda 환경
conda env list
conda activate [콘다명]

# 백엔드 서버 실행 명령어
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ai 서버 실행 명령어
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# cloudflared tunnel 실행 명령어
cloudflared tunnel run factoryguard-api