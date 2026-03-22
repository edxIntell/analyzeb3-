import streamlit as st
import requests

st.title("Debug — brapi.dev")
ticker = st.text_input("Ticker", value="BRKM5")

if st.button("Testar brapi com token"):
    symbol = ticker.upper().replace(".SA","")
    try:
        token = st.secrets["BRAPI_TOKEN"]
        st.success(f"Token encontrado: {token[:6]}...")
    except:
        st.error("BRAPI_TOKEN não encontrado nos secrets!")
        st.stop()

    url = f"https://brapi.dev/api/quote/{symbol}"
    params = {"range": "1mo", "interval": "1d", "fundamental": "false", "token": token}
    r = requests.get(url, params=params, timeout=20)
    st.write("Status:", r.status_code)

    if r.status_code == 200:
        results = r.json().get("results", [])
        if results:
            hist = results[0].get("historicalDataPrice") or []
            price = results[0].get("regularMarketPrice")
            st.success(f"OK — {len(hist)} candles — preço atual: R$ {price}")
            if hist:
                st.write("Último candle:", hist[-1])
        else:
            st.error("results vazio")
            st.json(r.json())
    else:
        st.error(r.text[:400])
