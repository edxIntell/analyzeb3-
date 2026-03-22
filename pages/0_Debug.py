import streamlit as st
import requests

st.title("Debug — Dividendos")
ticker = st.text_input("Ticker", value="TAEE11")

if st.button("Inspecionar campos de dividendo"):
    symbol = ticker.upper().replace(".SA", "")
    
    # Sem fundamental
    url1 = f"https://brapi.dev/api/quote/{symbol}?fundamental=false"
    r1 = requests.get(url1, timeout=15).json()
    res1 = (r1.get("results") or [{}])[0]
    
    # Com fundamental
    url2 = f"https://brapi.dev/api/quote/{symbol}?fundamental=true"
    r2 = requests.get(url2, timeout=15).json()
    res2 = (r2.get("results") or [{}])[0]

    st.subheader("Campos relevantes (sem fundamental)")
    for k in ["dividendYield", "dividendsPerShare", "lastDividendValue", 
              "regularMarketPrice", "currentPrice"]:
        st.write(f"`{k}` →", res1.get(k, "❌ ausente"))

    st.subheader("Campos relevantes (com fundamental=true)")
    for k in ["dividendYield", "dividendsPerShare", "lastDividendValue",
              "regularMarketPrice", "currentPrice", "trailingAnnualDividendRate",
              "trailingAnnualDividendYield"]:
        st.write(f"`{k}` →", res2.get(k, "❌ ausente"))

    st.subheader("Todos os campos retornados (fundamental=true)")
    st.json({k: v for k, v in res2.items() if v is not None and k != "historicalDataPrice"})
