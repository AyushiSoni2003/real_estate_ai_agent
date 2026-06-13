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


# Register API route modules
from app.api.v1 import auth, leads, properties, appointments, messages, property_media, ai_interactions, follow_up_logs, lead_activities

# Include all routers with /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(leads.router, prefix="/api/v1")
app.include_router(properties.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(property_media.router, prefix="/api/v1")
app.include_router(ai_interactions.router, prefix="/api/v1")
app.include_router(follow_up_logs.router, prefix="/api/v1")
app.include_router(lead_activities.router, prefix="/api/v1")
