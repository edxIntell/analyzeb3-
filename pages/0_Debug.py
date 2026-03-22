import streamlit as st
import requests
import pandas as pd

st.title("Debug — estrutura Yahoo")
ticker = st.text_input("Ticker", value="BRKM5")

if st.button("Inspecionar resposta Yahoo"):
    symbol = ticker.upper().replace(".SA","") + ".SA"
    ua = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    r = requests.get(url, headers=ua, timeout=20)
    st.write("Status:", r.status_code)
    if r.status_code == 200:
        result = r.json().get("chart",{}).get("result",[])
        if result:
            r0 = result[0]
            ind = r0.get("indicators",{})
            q   = ind.get("quote",[{}])[0]
            adj = ind.get("adjclose",[{}])
            st.write("timestamps:", len(r0.get("timestamp",[])))
            st.write("quote keys:", list(q.keys()))
            st.write("close sample:", q.get("close",[])[:3])
            st.write("adjclose present:", bool(adj))
            if adj:
                st.write("adjclose sample:", adj[0].get("adjclose",[])[:3])
        else:
            st.error("sem result")
            st.json(r.json())
    else:
        st.error(r.text[:300])
