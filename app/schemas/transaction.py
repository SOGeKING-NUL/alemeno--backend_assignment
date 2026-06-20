from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TransactionResponse(BaseModel):
    id: int
    txn_id: Optional[str] = None
    date: Optional[datetime] = None
    merchant: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    account_id: Optional[str] = None
    is_anomaly: bool
    anomaly_reason: Optional[str] = None

    class Config:
        from_attributes = True

class JobSummaryResponse(BaseModel):
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: Optional[List[Dict[str, Any]]] = None
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True

class JobResultResponse(BaseModel):
    job_id: int
    status: str
    summary: Optional[JobSummaryResponse] = None
    transactions: Optional[List[TransactionResponse]] = None
    flagged_anomalies: Optional[List[TransactionResponse]] = None
    category_breakdown: Optional[Dict[str, float]] = None
