import streamlit as st
import requests
import pandas as pd

st.title("Debug — Teste direto")
ticker = st.text_input("Ticker", value="VALE3")

if st.button("Testar fetch completo"):
    symbol = ticker.upper().replace(".SA", "")
    url = f"https://brapi.dev/api/quote/{symbol}?range=1y&interval=1d&fundamental=false"
    
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        results = data.get("results", [])
        
        if not results:
            st.error("Sem results na resposta")
            st.json(data)
            st.stop()
            
        hist = results[0].get("historicalDataPrice") or []
        st.write(f"Candles recebidos: {len(hist)}")
        
        rows = []
        erros = []
        for h in hist:
            close_val = h.get("close") or h.get("adjustedClose")
            if close_val is not None:
                try:
                    date_val = pd.to_datetime(h["date"], unit="s") if isinstance(h["date"], (int, float)) else pd.to_datetime(h["date"])
                    rows.append({"Date": date_val, "Open": h.get("open") or close_val,
                                 "High": h.get("high") or close_val, "Low": h.get("low") or close_val,
                                 "Close": close_val, "Volume": h.get("volume") or 0})
                except Exception as e:
                    erros.append(str(e))
        
        if erros:
            st.warning(f"Erros no parse: {erros[:3]}")
        
        if rows:
            df = pd.DataFrame(rows).set_index("Date").sort_index()
            st.success(f"DataFrame OK — {len(df)} linhas — último: {df.index[-1].date()} close={df['Close'].iloc[-1]:.2f}")
            st.dataframe(df.tail(5))
        else:
            st.error("Nenhuma linha válida construída")
            st.write("Primeiro candle raw:", hist[0] if hist else "vazio")
            
    except Exception as e:
        st.error(f"Exceção: {type(e).__name__}: {e}")
