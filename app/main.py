from fastapi import FastAPI
from app.api.routes import api_router
from app.core.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# Create all tables in the database (simple migration)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transaction Processing Pipeline",
    description="AI-Powered Transaction Processing Pipeline",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Transaction Processing Pipeline API"}
