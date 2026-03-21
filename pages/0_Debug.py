import streamlit as st
import requests
import pandas as pd

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
            hist = r.get("historicalDataPrice") or []
            st.success(f"Brapi OK — {len(hist)} candles")
            if hist:
                st.write("Primeiro candle (estrutura):", hist[0])
                st.write("Último candle:", hist[-1])
                rows = []
                for h in hist:
                    close_val = h.get("close") or h.get("adjustedClose")
                    if close_val:
                        try:
                            date_val = pd.to_datetime(h["date"], unit="s") if isinstance(h["date"], (int,float)) else pd.to_datetime(h["date"])
                            rows.append({"Date": date_val, "Close": close_val})
                        except: pass
                if rows:
                    df = pd.DataFrame(rows).set_index("Date")
                    st.success(f"DataFrame OK — {len(df)} linhas")
                    st.dataframe(df.tail(5))
                else:
                    st.error("Nenhuma linha válida no histórico")
        else:
            st.error("Sem results")
            st.json(data)
    except Exception as e:
        st.error(f"Erro: {e}")
