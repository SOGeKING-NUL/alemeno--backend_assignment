from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    txn_id = Column(String, index=True, nullable=True)
    date = Column(DateTime(timezone=True), nullable=True)
    merchant = Column(String, index=True, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True)
    category = Column(String, nullable=True)
    account_id = Column(String, index=True, nullable=True)
    
    # Anomaly tracking
    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String, nullable=True)
    
    # LLM classification
    llm_category = Column(String, nullable=True)
    llm_raw_response = Column(String, nullable=True)
    llm_failed = Column(Boolean, default=False)
