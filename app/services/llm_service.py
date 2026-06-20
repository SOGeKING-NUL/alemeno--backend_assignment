import json
from openai import OpenAI
from app.core.config import settings

def get_llm_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API,
    )

def classify_transactions(transactions_data: list[dict]) -> dict:
    """
    Call OpenRouter LLM to classify a batch of transactions.
    """
    if not transactions_data:
        return {}

    client = get_llm_client()
    
    prompt = f"""
    You are a financial transaction categorizer. Categorize the following transactions into exactly ONE of these categories:
    Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other.
    
    Transactions:
    {json.dumps(transactions_data, indent=2)}
    
    Return a valid JSON object where keys are the txn_id and values are the assigned category.
    Do not wrap in markdown tags like ```json ... ```, just output the raw JSON object.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    try:
        text = response.choices[0].message.content.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response for classification: {e}\nResponse text: {response.choices[0].message.content}")


def generate_narrative_summary(total_inr: float, total_usd: float, top_merchants: list, anomaly_count: int) -> tuple[str, str]:
    """
    Call OpenRouter LLM to generate a narrative summary and risk level.
    Returns (narrative, risk_level)
    """
    client = get_llm_client()
    
    prompt = f"""
    Analyze the following transaction batch summary and provide a spending narrative and a risk level.
    
    Data:
    - Total Spend (INR): {total_inr}
    - Total Spend (USD): {total_usd}
    - Top 3 Merchants: {json.dumps(top_merchants)}
    - Anomaly Count: {anomaly_count}
    
    Provide a 2-3 sentence spending narrative summarizing the trends.
    Assign a risk_level of "low", "medium", or "high" based on the anomalies and spending.
    
    Return exactly a JSON object with keys "narrative" and "risk_level".
    Do not wrap in markdown tags, just the raw JSON.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    try:
        text = response.choices[0].message.content.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        result = json.loads(text.strip())
        return result.get("narrative", ""), result.get("risk_level", "low")
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response for summary: {e}\nResponse text: {response.choices[0].message.content}")

