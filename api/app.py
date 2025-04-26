from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import drug, drug_class, analytics
from models import init_db

# Initialize the FastAPI app
app = FastAPI(
    title="Protego HW API",
    description="API for Protego HW - Drug and Analytics Data",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drug.router)
app.include_router(drug_class.router)
app.include_router(analytics.router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "Welcome to the Protego HW API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.on_event("startup")
def startup_event():
    """Initialize the database on startup."""
    init_db()
