import pandas as pd
from datetime import datetime
from celery.utils.log import get_task_logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.worker.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary

from app.services.data_cleaner import clean_data
from app.services.anomaly_detector import detect_anomalies
from app.services.llm_service import classify_transactions, generate_narrative_summary

logger = get_task_logger(__name__)

# Using tenacity for exponential backoff on LLM classification
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def classify_with_retry(batch):
    return classify_transactions(batch)

@celery_app.task(bind=True, name="process_transaction_file")
def process_transaction_file(self, job_id: int, file_path: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found.")
        db.close()
        return

    try:
        job.status = "processing"
        db.commit()

        # 1. Load data
        df = pd.read_csv(file_path)
        job.row_count_raw = len(df)
        
        # 2. Clean data
        df = clean_data(df)
        job.row_count_clean = len(df)
        
        # 3. Anomaly detection
        df = detect_anomalies(df)
        
        # 4. LLM Classification (batching transactions with 'Uncategorised')
        uncategorised_df = df[df['category'] == 'Uncategorised']
        
        if not uncategorised_df.empty:
            # Prepare batch
            batch_for_llm = uncategorised_df[['txn_id', 'merchant', 'amount', 'notes']].fillna('').to_dict(orient='records')
            
            try:
                # Call LLM with retry
                classification_results = classify_with_retry(batch_for_llm)
                
                # Apply results
                for txn_id, llm_cat in classification_results.items():
                    if pd.notna(txn_id):
                        df.loc[df['txn_id'] == txn_id, 'category'] = llm_cat
                        df.loc[df['txn_id'] == txn_id, 'llm_category'] = llm_cat
                        
            except Exception as e:
                logger.error(f"LLM Classification failed after retries for Job {job_id}: {e}")
                df.loc[df['category'] == 'Uncategorised', 'llm_failed'] = True

        # 5. Save Transactions to DB
        # Replace NaNs with None for DB insertion
        df = df.replace({pd.NA: None, float('nan'): None})
        
        transactions_to_insert = []
        total_inr = 0.0
        total_usd = 0.0
        merchant_spend = {}
        anomaly_count = int(df['is_anomaly'].sum())
        
        for _, row in df.iterrows():
            txn = Transaction(
                job_id=job_id,
                txn_id=str(row.get('txn_id')) if row.get('txn_id') else None,
                date=row.get('date') if pd.notnull(row.get('date')) else None,
                merchant=str(row.get('merchant')) if row.get('merchant') else None,
                amount=float(row.get('amount')) if row.get('amount') else 0.0,
                currency=str(row.get('currency')) if row.get('currency') else None,
                status=str(row.get('status')) if row.get('status') else None,
                category=str(row.get('category')) if row.get('category') else None,
                account_id=str(row.get('account_id')) if row.get('account_id') else None,
                is_anomaly=bool(row.get('is_anomaly', False)),
                anomaly_reason=str(row.get('anomaly_reason')) if row.get('anomaly_reason') else None,
                llm_category=str(row.get('llm_category')) if row.get('llm_category') else None,
                llm_failed=bool(row.get('llm_failed', False))
            )
            transactions_to_insert.append(txn)
            
            # Aggregate stats for summary
            amount = txn.amount or 0.0
            if txn.currency == 'INR':
                total_inr += amount
            elif txn.currency == 'USD':
                total_usd += amount
                
            if txn.merchant:
                merchant_spend[txn.merchant] = merchant_spend.get(txn.merchant, 0.0) + amount

        db.add_all(transactions_to_insert)
        
        # 6. Generate Summary
        # Top 3 merchants
        top_merchants = sorted(merchant_spend.items(), key=lambda x: x[1], reverse=True)[:3]
        top_merchants_list = [{"merchant": k, "spend": v} for k, v in top_merchants]
        
        narrative, risk_level = "", "low"
        try:
            narrative, risk_level = generate_narrative_summary(total_inr, total_usd, top_merchants_list, anomaly_count)
        except Exception as e:
            logger.error(f"LLM Summary generation failed for Job {job_id}: {e}")
            
        summary = JobSummary(
            job_id=job_id,
            total_spend_inr=total_inr,
            total_spend_usd=total_usd,
            top_merchants=top_merchants_list,
            anomaly_count=anomaly_count,
            narrative=narrative,
            risk_level=risk_level
        )
        db.add(summary)
        
        # 7. Finalize Job
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed with error: {str(e)}")
        db.rollback()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
