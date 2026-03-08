from auth import get_kotak_client
from market_data import fetch_nse_fo_master

def main():
    # 1. Authenticate and get the client instance
    client = get_kotak_client()
    
    if not client:
        print("Exiting application because login failed.")
        return

    # 2. Verify connection by fetching limits
    limits = client.limits()
    if limits and limits.get('stat') == 'Ok':
        print("✅ Account Data Fetched Successfully.")
        
    # 3. Fetch and load the F&O Contract Master
    df_fo = fetch_nse_fo_master(client)
    
    if df_fo is not None:
        print("\nHere are the columns available in the F&O master:")
        print(list(df_fo.columns))

if __name__ == "__main__":
    main()