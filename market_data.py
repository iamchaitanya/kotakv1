import io
import time
import requests
import pandas as pd

def fetch_scrip_master(client, segment="bse_fo.csv"):
    """Fetches the specified scrip master (bse_fo or nse_fo)."""
    try:
        master_data = client.scrip_master()
        file_url = next((url for url in master_data.get('filesPaths', []) if segment in url), None)
        
        if not file_url:
            print(f"❌ Could not find the {segment} URL.")
            return None
            
        response = requests.get(file_url)
        if response.status_code == 200:
            return pd.read_csv(io.StringIO(response.text), low_memory=False)
        return None
    except Exception as e:
        print(f"❌ Error fetching master: {e}")
        return None

def get_nearest_sensex_options(df):
    """Filters the BSE F&O master for the nearest SENSEX expiry."""
    
    # 0. THE MAGIC FIX: Scrub Kotak's messy column names!
    # This removes trailing spaces (like 'lExpiryDate ') and semicolons (like 'dStrikePrice;')
    df.columns = df.columns.str.strip().str.replace(';', '')
    
    # 1. Look for 'SENSEX' or 'BSX'
    mask_name = df['pSymbolName'].astype(str).str.upper().isin(['SENSEX', 'BSX'])
    mask_trd_sensex = df['pTrdSymbol'].astype(str).str.upper().str.startswith('SENSEX')
    mask_trd_bsx = df['pTrdSymbol'].astype(str).str.upper().str.startswith('BSX')
    
    df_sensex = df[mask_name | mask_trd_sensex | mask_trd_bsx].copy()
    
    # 2. Keep only Call (CE) and Put (PE) options
    if 'pOptionType' in df_sensex.columns:
        df_sensex = df_sensex[df_sensex['pOptionType'].isin(['CE', 'PE'])]
    
    if df_sensex.empty:
        return None
        
    # 3. Handle the Expiry Date smartly (now that the columns are clean)
    if 'lExpiryDate' in df_sensex.columns:
        current_time = int(time.time())
        df_future = df_sensex[df_sensex['lExpiryDate'] >= (current_time - 86400)]
        if not df_future.empty:
            nearest_expiry = df_future['lExpiryDate'].min()
            df_nearest = df_future[df_future['lExpiryDate'] == nearest_expiry]
        else:
            df_nearest = df_sensex
            
    elif 'pExpiryDate' in df_sensex.columns: 
        df_sensex['ParsedExpiry'] = pd.to_datetime(df_sensex['pExpiryDate'], format='mixed', dayfirst=True, errors='coerce')
        df_sensex = df_sensex.dropna(subset=['ParsedExpiry'])
        today = pd.Timestamp.today().normalize()
        df_future = df_sensex[df_sensex['ParsedExpiry'] >= today]
        
        if not df_future.empty:
            nearest_expiry = df_future['ParsedExpiry'].min()
            df_nearest = df_future[df_future['ParsedExpiry'] == nearest_expiry]
        else:
            df_nearest = df_sensex
    else:
        return None

    # 4. Format and Sort beautifully by Strike Price
    if 'dStrikePrice' in df_nearest.columns:
        # Convert strike prices to numbers, divide by 100 to fix BSE formatting, and sort
        df_nearest['dStrikePrice'] = pd.to_numeric(df_nearest['dStrikePrice'], errors='coerce') / 100
        df_nearest = df_nearest.sort_values(by=['dStrikePrice', 'pOptionType'])
        
    # 5. Convert the Unix timestamp into a readable date (e.g., 13-Mar-2026)
    # We check for both lExpiryDate and pExpiryDate depending on what Kotak gave us today
    if 'pExpiryDate' in df_nearest.columns and pd.api.types.is_numeric_dtype(df_nearest['pExpiryDate']):
        df_nearest['pExpiryDate'] = pd.to_datetime(df_nearest['pExpiryDate'], unit='s').dt.strftime('%d-%b-%Y')
    elif 'lExpiryDate' in df_nearest.columns and pd.api.types.is_numeric_dtype(df_nearest['lExpiryDate']):
        df_nearest['lExpiryDate'] = pd.to_datetime(df_nearest['lExpiryDate'], unit='s').dt.strftime('%d-%b-%Y')
        
    # 6. Clean up the table for the dashboard
    cols_to_show = [
        'pTrdSymbol',   
        'pSymbolName',  
        'dStrikePrice', 
        'pOptionType',  
        'pExpiryDate' if 'pExpiryDate' in df_nearest.columns else 'lExpiryDate',
        'pSymbol'       
    ]
    
    # Only keep the columns that actually exist to avoid crashes
    cols_to_show = [c for c in cols_to_show if c in df_nearest.columns]
    
    return df_nearest[cols_to_show]