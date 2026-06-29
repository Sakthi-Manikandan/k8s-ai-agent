from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.logger import log
from backend.core.settings import settings


# Create FastAPI app
app = FastAPI(
    title="K8s AI Agent",
    description="AI-powered Kubernetes troubleshooting agent that automatically investigates and diagnoses cluster failures",
    version="1.0.0"
)

# Add CORS middleware
# This allows our Streamlit frontend
# to talk to our FastAPI backend!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register our routes
app.include_router(router, prefix="/api/v1")


@app.get("/startup")
async def startup_event():
    from backend.db.database import init_database
    init_database()
    log.info("Database initialised!")
    """
    Runs when FastAPI starts up!
    Like a welcome message!
    """
    log.info("=" * 50)
    log.info("🤖 K8s AI Agent Starting...")
    log.info(f"Environment: {settings.APP_ENV}")
    log.info(f"Host: {settings.APP_HOST}")
    log.info(f"Port: {settings.APP_PORT}")
    log.info(f"LLM Model: {settings.OLLAMA_MODEL}")
    log.info("=" * 50)


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "service": "K8s AI Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )