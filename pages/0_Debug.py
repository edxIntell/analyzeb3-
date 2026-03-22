import streamlit as st
import requests

st.title("Debug — Fontes de dados")
ticker = st.text_input("Ticker", value="VALE3")

if st.button("Testar endpoint de dividendos brapi"):
    symbol = ticker.upper().replace(".SA","")
    url = f"https://brapi.dev/api/quote/{symbol}/dividends"
    r = requests.get(url, timeout=15)
    st.write("Status:", r.status_code)
    st.json(r.json())

if st.button("Testar yfinance .info"):
    try:
        import yfinance as yf
        t = yf.Ticker(ticker if ticker.endswith(".SA") else ticker+".SA")
        info = t.info
        for k in ["dividendYield","trailingAnnualDividendRate","trailingAnnualDividendYield",
                  "lastDividendValue","dividendsPerShare","trailingEps","bookValue",
                  "freeCashflow","ebitda","totalDebt","totalCash","sharesOutstanding",
                  "returnOnEquity","priceToBook","trailingPE","currentPrice","regularMarketPrice"]:
            st.write(f"`{k}` →", info.get(k, "❌ ausente"))
    except Exception as e:
        st.error(f"yfinance erro: {e}")

if st.button("Testar Yahoo Finance direto (sem yfinance)"):
    symbol = ticker.upper().replace(".SA","") + ".SA"
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=summaryDetail,defaultKeyStatistics,financialData,incomeStatementHistory"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    st.write("Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        result = data.get("quoteSummary",{}).get("result",[{}])
        if result:
            sd = result[0].get("summaryDetail",{})
            fd = result[0].get("financialData",{})
            for k in ["dividendYield","trailingAnnualDividendRate","dividendRate"]:
                st.write(f"summaryDetail.{k} →", sd.get(k,{}).get("raw","❌"))
            for k in ["freeCashflow","totalDebt","totalCash","revenueGrowth","earningsGrowth"]:
                st.write(f"financialData.{k} →", fd.get(k,{}).get("raw","❌"))
    else:
        st.error(r.text[:300])
