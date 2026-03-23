import streamlit as st
import requests
import pandas as pd

st.title("Debug — Alpha Vantage")
ticker = st.text_input("Ticker", value="BRKM5")

if st.button("Testar Alpha Vantage com chave"):
    key = st.secrets.get("ALPHAVANTAGE_KEY", "")
    if not key:
        st.error("ALPHAVANTAGE_KEY não encontrada nos Secrets!")
        st.stop()
    st.success(f"Chave encontrada: {key[:6]}...")

    symbol = ticker.upper().replace(".SA","") + ".SAO"
    url = "https://www.alphavantage.co/query"
    params = {"function": "TIME_SERIES_DAILY", "symbol": symbol,
              "outputsize": "compact", "apikey": key}
    r = requests.get(url, params=params, timeout=20)
    st.write("Status:", r.status_code)
    data = r.json()
    ts = data.get("Time Series (Daily)")
    if ts:
        dates = sorted(ts.keys(), reverse=True)
        st.success(f"OK — {len(dates)} dias. Último: {dates[0]}")
        st.write(ts[dates[0]])
    else:
        st.error("Sem Time Series")
        st.json(data)
