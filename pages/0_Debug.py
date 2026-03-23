import streamlit as st
import requests
import pandas as pd

st.title("Debug — teste de fontes")
ticker = st.text_input("Ticker", value="BRKM5")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Testar yfinance"):
        try:
            import yfinance as yf
            sym = ticker.upper().replace(".SA","") + ".SA"
            df = yf.download(sym, period="1mo", progress=False, threads=False, auto_adjust=True)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                st.success(f"yfinance OK — {len(df)} linhas")
                st.write(df.tail(3))
            else:
                st.error("yfinance retornou vazio")
        except Exception as e:
            st.error(f"yfinance erro: {e}")

with col2:
    if st.button("Testar HG Brasil"):
        sym = ticker.upper().replace(".SA","")
        url = f"https://api.hgbrasil.com/finance/stock_price?key=demo&symbol={sym}"
        try:
            r = requests.get(url, timeout=10)
            st.write("Status:", r.status_code)
            d = r.json()
            st.json(d)
        except Exception as e:
            st.error(f"HG Brasil erro: {e}")

with col3:
    if st.button("Testar Alpha Vantage"):
        sym = ticker.upper().replace(".SA","") + ".SAO"
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={sym}&apikey=demo&outputsize=compact"
        try:
            r = requests.get(url, timeout=15)
            st.write("Status:", r.status_code)
            d = r.json()
            keys = list(d.keys())
            st.write("keys:", keys)
            if "Time Series (Daily)" in d:
                dates = list(d["Time Series (Daily)"].keys())
                st.success(f"Alpha Vantage OK — {len(dates)} dias")
                st.write("Último:", dates[0], d["Time Series (Daily)"][dates[0]])
            else:
                st.json(d)
        except Exception as e:
            st.error(f"Alpha Vantage erro: {e}")
