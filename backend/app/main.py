"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered real estate automation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,   # Allows: Cookies ,Authentication tokens ,Sessions to be sent.
    allow_methods=["*"], #Allows all HTTP methods
    allow_headers=["*"], #Allows all request headers.  Authorization, Content-Type , X-API-Key
)

# Why use Health Checks?
# Very common in production.
# Docker, Kubernetes, Render, Railway, etc. check:
# to verify:
# ✅ Server is running
# ✅ Application started successfully
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/")
async def root():
    return {"message": "RealtyIQ API is running"}
