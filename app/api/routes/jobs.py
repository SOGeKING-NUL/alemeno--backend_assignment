import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.schemas.job import JobResponse, JobUploadResponse, JobStatusResponse
from app.schemas.transaction import JobResultResponse
from app.worker.tasks import process_transaction_file
import time


router = APIRouter()

UPLOAD_DIR = "uploads"

@router.post("/upload", response_model=JobUploadResponse)
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, f"{file.filename}")
    # Handle duplicates by adding timestamp if needed, but for now just overwrite
    file_path = os.path.join(UPLOAD_DIR, f"{int(time.time())}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create Job record
    new_job = Job(filename=file.filename, status="pending")
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Enqueue celery task
    process_transaction_file.delay(new_job.id, file_path)
    
    return {"job_id": new_job.id}

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    summary = None
    if job.status == "completed":
        summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
        
    response_data = {
        "id": job.id,
        "filename": job.filename,
        "status": job.status,
        "row_count_raw": job.row_count_raw,
        "row_count_clean": job.row_count_clean,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message,
        "summary": summary
    }
    return JobStatusResponse(**response_data)

@router.get("/{job_id}/results", response_model=JobResultResponse)
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "completed":
        return JobResultResponse(
            job_id=job.id,
            status=job.status,
            summary=None,
            transactions=None
        )
        
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    
    flagged_anomalies = [t for t in transactions if t.is_anomaly]
    
    category_breakdown = {}
    for t in transactions:
        cat = t.category or "Uncategorised"
        amount = t.amount or 0.0
        category_breakdown[cat] = category_breakdown.get(cat, 0.0) + amount
        
    # Round the values for cleaner output
    category_breakdown = {k: round(v, 2) for k, v in category_breakdown.items()}
    
    return JobResultResponse(
        job_id=job.id,
        status=job.status,
        summary=summary,
        transactions=transactions,
        flagged_anomalies=flagged_anomalies,
        category_breakdown=category_breakdown
    )

@router.get("", response_model=List[JobResponse])
def list_jobs(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.order_by(Job.created_at.desc()).all()
    return jobs
