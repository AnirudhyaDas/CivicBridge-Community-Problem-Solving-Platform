from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

# Import from app_backend
from app_backend.database import Base, engine
from app_backend.models import user, problem, solution, token_blacklist
from app_backend.routes import users, auth, problems, solutions, admin

# Create tables
Base.metadata.create_all(bind=engine)

app_backend = FastAPI(
    title="CivicBridge",
    description="Community Problem-Solving Marketplace API",
    version="1.0.0"
)

# Add CORS middleware
app_backend.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app_backend.include_router(auth.router)
app_backend.include_router(users.router)
app_backend.include_router(problems.router)
app_backend.include_router(solutions.router)
app_backend.include_router(admin.router)

# Root endpoint
@app_backend.get("/")
def root():
    return {"message": "CivicBridge API is running"}