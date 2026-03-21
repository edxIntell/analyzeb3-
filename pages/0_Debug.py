import streamlit as st
import requests

st.title("Debug — Teste de conexão")

ticker = st.text_input("Ticker", value="VALE3")

if st.button("Testar brapi.dev"):
    url = f"https://brapi.dev/api/quote/{ticker}?range=1mo&interval=1d&fundamental=false"
    st.code(url)
    try:
        resp = requests.get(url, timeout=15)
        st.write("Status:", resp.status_code)
        data = resp.json()
        results = data.get("results", [])
        if results:
            r = results[0]
            hist = r.get("historicalDataPrice", [])
            st.success(f"Brapi OK — {len(hist)} candles recebidos")
            st.json(r.get("regularMarketPrice"))
        else:
            st.error("Brapi retornou vazio")
            st.json(data)
    except Exception as e:
        st.error(f"Brapi falhou: {e}")

if st.button("Testar yfinance"):
    try:
        import yfinance as yf
        df = yf.download(ticker + ".SA", period="1mo", progress=False, threads=False)
        if df is not None and not df.empty:
            st.success(f"yfinance OK — {len(df)} linhas")
            st.dataframe(df.tail(3))
        else:
            st.error("yfinance retornou vazio")
    except Exception as e:
        st.error(f"yfinance falhou: {e}")
