from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import canvas, emails, insights, regrade

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emails.router, prefix="/emails", tags=["emails"])
app.include_router(canvas.router, prefix="/canvas", tags=["canvas"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(regrade.router, prefix="/regrade", tags=["regrade"])

@app.get("/health")
def health():
    return {"status": "ok"}
