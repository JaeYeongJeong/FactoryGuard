from fastapi import FastAPI

from app.routers import web

app = FastAPI()

app.include_router(web.router)

@app.get("/health")
def health_check():
    return {"status": "ai server ok"}
