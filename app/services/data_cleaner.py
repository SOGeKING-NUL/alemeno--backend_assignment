import pandas as pd
import numpy as np

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the transactions DataFrame according to requirements:
    - Normalize date formats to ISO 8601
    - Strip currency symbols from amounts
    - Uppercase status values
    - Fill missing categories with 'Uncategorised'
    - Remove exact duplicate rows
    """
    
    # 1. Drop duplicate rows
    df = df.drop_duplicates()
    
    # 2. Normalize date formats to ISO 8601
    if 'date' in df.columns:
        # pd.to_datetime handles mixed formats if dayfirst is specified carefully or just let it infer
        # The prompt says DD-MM-YYYY and YYYY/MM/DD both appear. 
        # Using format='mixed' is supported in newer pandas versions.
        df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True, errors='coerce')
    
    # 3. Strip currency symbols from amounts
    if 'amount' in df.columns:
        # Convert to string, replace $, convert to float
        df['amount'] = df['amount'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
    # 4. Currency inconsistent casing
    if 'currency' in df.columns:
        df['currency'] = df['currency'].astype(str).str.upper()
        
    # 5. Uppercase status values
    if 'status' in df.columns:
        df['status'] = df['status'].astype(str).str.upper()
        
    # 6. Fill missing categories with 'Uncategorised'
    if 'category' in df.columns:
        # Replace empty strings and nans
        df['category'] = df['category'].replace(r'^\s*$', np.nan, regex=True)
        df.loc[:, 'category'] = df['category'].fillna('Uncategorised')
        
    return df
