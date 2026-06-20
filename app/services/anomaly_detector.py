import pandas as pd

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect anomalies in the cleaned DataFrame:
    - Flag transactions where amount exceeds 3x the account's median.
    - Flag rows where currency is USD but the merchant is a domestic-only brand.
    """
    df['is_anomaly'] = False
    df['anomaly_reason'] = ""
    
    # Ensure amount is numeric for calculation
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

    # 1. Statistical Outlier: amount > 3x account's median
    # Calculate median per account
    if 'account_id' in df.columns and 'amount' in df.columns:
        medians = df.groupby('account_id')['amount'].transform('median')
        outlier_mask = df['amount'] > (3 * medians)
        
        df.loc[outlier_mask, 'is_anomaly'] = True
        df.loc[outlier_mask, 'anomaly_reason'] = df.loc[outlier_mask, 'anomaly_reason'] + "Amount > 3x account median. "
        
    # 2. Currency/Merchant Mismatch: USD and domestic merchant
    domestic_merchants = ['SWIGGY', 'OLA', 'IRCTC']
    if 'currency' in df.columns and 'merchant' in df.columns:
        # Clean merchant for comparison
        clean_merchant = df['merchant'].astype(str).str.upper().str.strip()
        mismatch_mask = (df['currency'] == 'USD') & clean_merchant.isin(domestic_merchants)
        
        df.loc[mismatch_mask, 'is_anomaly'] = True
        df.loc[mismatch_mask, 'anomaly_reason'] = df.loc[mismatch_mask, 'anomaly_reason'] + "USD used for domestic merchant. "

    df['anomaly_reason'] = df['anomaly_reason'].str.strip()
    return df
