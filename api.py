from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

# Import your existing Kotak logic
from auth import get_kotak_client
from market_data import fetch_scrip_master, get_nearest_sensex_options

app = FastAPI(title="Kotak Trading API")

# Allow React to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # React usually runs on localhost:5173 or 3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold the Kotak client session
kotak_client = None

@app.get("/")
def read_root():
    return {"status": "Online", "message": "Kotak API Engine is running"}

@app.post("/login")
def login_kotak():
    global kotak_client
    try:
        kotak_client = get_kotak_client()
        if kotak_client:
            return {"status": "success", "message": "Logged into Kotak Neo"}
        else:
            raise HTTPException(status_code=401, detail="Kotak login failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/limits")
def get_limits():
    if not kotak_client:
        raise HTTPException(status_code=401, detail="Not logged in")
    return kotak_client.limits()

@app.get("/sensex-options")
def get_sensex_options():
    if not kotak_client:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    df_bse = fetch_scrip_master(kotak_client, segment="bse_fo.csv")
    if df_bse is None:
        raise HTTPException(status_code=500, detail="Failed to fetch BSE Master")
        
    df_sensex = get_nearest_sensex_options(df_bse)
    if df_sensex is None or df_sensex.empty:
        return {"status": "success", "data": []}
        
    # Convert Pandas DataFrame to JSON for React
    return {"status": "success", "data": df_sensex.to_dict(orient="records")}

@app.get("/signals")
def get_live_signals():
    """React will call this to get the latest Telegram signals."""
    if not os.path.exists("live_signals.json"):
        return {"status": "success", "data": []}
        
    with open("live_signals.json", "r") as f:
        try:
            signals = json.load(f)
            return {"status": "success", "data": signals}
        except json.JSONDecodeError:
            return {"status": "success", "data": []}

if __name__ == "__main__":
    import uvicorn
    # Runs the API on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000, ws="none")