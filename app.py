import streamlit as st
import pandas as pd
from auth import get_kotak_client
from market_data import fetch_scrip_master, get_nearest_sensex_options

st.set_page_config(page_title="Kotak Neo Bot", layout="wide")

st.title("📈 Kotak Neo Trading Dashboard")

if "client" not in st.session_state:
    st.session_state.client = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Connection")
    if st.button("Login to Kotak API"):
        with st.spinner("Authenticating via TOTP..."):
            client = get_kotak_client()
            if client:
                st.session_state.client = client
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Login failed. Check your terminal logs.")

# --- MAIN PAGE ---
if st.session_state.client:
    client = st.session_state.client
    
    # THIS is the line that was missing or misplaced!
    tab1, tab2 = st.tabs(["📊 Account Limits", "🎯 SENSEX Options"])
    
    with tab1:
        st.subheader("Live Account Margins & Limits")
        if st.button("Fetch Limits"):
            with st.spinner("Fetching data from Kotak..."):
                limits = client.limits()
                st.json(limits) 
                
    with tab2:
        st.subheader("🎯 Nearest SENSEX Expiry")
        st.write("Automatically fetches the BSE master and filters for the closest SENSEX expiry.")
        
        if st.button("Get SENSEX Options"):
            with st.spinner("Downloading BSE Master and filtering..."):
                df_bse = fetch_scrip_master(client, segment="bse_fo.csv")
                
                if df_bse is not None:
                    df_sensex_nearest = get_nearest_sensex_options(df_bse)
                    
                    if df_sensex_nearest is not None and not df_sensex_nearest.empty:
                        st.success(f"✅ Found {len(df_sensex_nearest)} contracts!")
                        st.dataframe(df_sensex_nearest, use_container_width=True)
                    else:
                        st.warning("⚠️ Could not find any active SENSEX options.")
else:
    st.info("👈 Please click 'Login to Kotak API' in the sidebar to start.")