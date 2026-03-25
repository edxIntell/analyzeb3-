import streamlit as st
import requests

st.title("Debug — Yahoo quoteSummary webscraping")
ticker = st.text_input("Ticker", value="BRKM5.SA")

if st.button("Testar quoteSummary"):
    symbol  = ticker.upper() if ticker.endswith(".SA") else ticker.upper() + ".SA"
    modules = "summaryDetail,defaultKeyStatistics,financialData,summaryProfile,price"
    url     = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules={modules}"
    headers = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept":          "application/json",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Referer":         "https://finance.yahoo.com/",
    }
    r = requests.get(url, headers=headers, timeout=20)
    st.write("Status:", r.status_code)
    if r.status_code == 200:
        result = r.json().get("quoteSummary", {}).get("result", [])
        if result:
            pr = result[0].get("price", {})
            fd = result[0].get("financialData", {})
            def raw(obj, k):
                v = obj.get(k)
                return v.get("raw") if isinstance(v, dict) else v
            st.success(f"OK! Nome: {pr.get('longName')} | Preço: {raw(pr,'regularMarketPrice')}")
            st.write("ROE:", raw(fd,"returnOnEquity"))
            st.write("Margem:", raw(fd,"profitMargins"))
            st.write("DY:", result[0].get("summaryDetail",{}).get("dividendYield",{}).get("raw"))
        else:
            st.error("Sem result")
            st.json(r.json())
    else:
        st.error(r.text[:300])
