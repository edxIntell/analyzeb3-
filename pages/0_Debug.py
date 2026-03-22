import streamlit as st
import requests
import pandas as pd

st.title("Debug — Fontes de preço")
ticker = st.text_input("Ticker", value="VALE3")

if st.button("Testar Yahoo chart API (direto)"):
    symbol = ticker.upper().replace(".SA","") + ".SA"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1mo"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    r = requests.get(url, headers=headers, timeout=20)
    st.write("Status:", r.status_code)
    if r.status_code == 200:
        result = r.json().get("chart",{}).get("result",[])
        if result:
            closes = result[0].get("indicators",{}).get("quote",[{}])[0].get("close",[])
            closes = [c for c in closes if c is not None]
            st.success(f"OK — {len(closes)} closes. Último: {closes[-1]:.2f}")
        else:
            st.error("Sem result")
            st.json(r.json())
    else:
        st.error(r.text[:300])

if st.button("Testar brapi"):
    symbol = ticker.upper().replace(".SA","")
    url = f"https://brapi.dev/api/quote/{symbol}?range=1mo&interval=1d"
    r = requests.get(url, timeout=15)
    st.write("Status:", r.status_code)
    if r.status_code == 200:
        results = r.json().get("results",[])
        if results:
            hist = results[0].get("historicalDataPrice",[]) or []
            st.success(f"OK — {len(hist)} candles")
        else:
            st.error("Sem results")
    else:
        st.error(r.text[:200])
