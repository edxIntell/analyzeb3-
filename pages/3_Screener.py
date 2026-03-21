import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import STYLE, fetch_price_history, fetch_fundamentals, calc_all_indicators, compute_all_scores, SAFE_TICKERS

st.set_page_config(page_title="Screener · AnalyzeB3", page_icon="📊", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:22px;margin-bottom:4px">AnalyzeB3</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#6b7080;letter-spacing:2px;text-transform:uppercase;margin-bottom:24px">Plataforma de análise</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:12px;color:var(--muted);margin-bottom:8px">FILTROS TÉCNICOS</div>', unsafe_allow_html=True)
    rsi_min, rsi_max = st.slider("RSI", 0, 100, (20, 70))
    price_above_ma20 = st.checkbox("Preço acima da MM20", value=False)
    price_above_ma200 = st.checkbox("Preço acima da MM200", value=False)

    st.markdown('<div style="font-size:12px;color:var(--muted);margin-top:16px;margin-bottom:8px">FILTROS FUNDAMENTALISTAS</div>', unsafe_allow_html=True)
    pe_max = st.number_input("P/L máximo", value=30.0, step=1.0)
    dy_min = st.number_input("Dividend Yield mín. (%)", value=0.0, step=0.5)
    roe_min = st.number_input("ROE mínimo (%)", value=0.0, step=1.0)

    st.markdown('<div style="font-size:12px;color:var(--muted);margin-top:16px;margin-bottom:8px">FILTROS DE SCORE</div>', unsafe_allow_html=True)
    score_lynch_min = st.slider("Score Lynch mínimo", 0, 100, 0)
    score_barsi_min = st.slider("Score Barsi mínimo", 0, 100, 0)
    score_dalio_min = st.slider("Score Dalio mínimo", 0, 100, 0)

    run = st.button("Rodar Screener", use_container_width=True)

    st.markdown("---")
    st.page_link("Home.py", label="Home")
    st.page_link("pages/1_Ficha_Ativo.py", label="Ficha de Ativo")
    st.page_link("pages/2_Comparativo.py", label="Comparativo Multi-Asset")
    st.page_link("pages/3_Screener.py", label="Screener")

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:32px">
    <div class="section-tag">SCREENER</div>
    <div class="section-title">Filtros combinados AT + AF + Frameworks</div>
</div>
""", unsafe_allow_html=True)

if not run:
    st.markdown(f"""
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:48px;text-align:center">
        <div style="font-family:'DM Serif Display',serif;font-size:28px;color:var(--muted);margin-bottom:12px">Configure os filtros e rode o screener</div>
        <div style="font-size:14px;color:var(--muted)">O screener analisa {len(SAFE_TICKERS)} ações da B3 com os critérios selecionados.</div>
        <div style="font-size:12px;color:#3d4050;margin-top:8px">Pode levar 30-60 segundos dependendo dos filtros.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─── RUN SCREENER ─────────────────────────────────────────────────────────────
results = []
progress_bar = st.progress(0)
status_text = st.empty()

for i, ticker in enumerate(SAFE_TICKERS):
    status_text.markdown(f'<div style="font-family:\'DM Mono\',monospace;font-size:11px;color:var(--muted)">Analisando {ticker}...</div>', unsafe_allow_html=True)
    progress_bar.progress((i + 1) / len(SAFE_TICKERS))

    try:
        df_raw = fetch_price_history(ticker, "1y")
        if df_raw.empty or len(df_raw) < 30:
            continue
        df = calc_all_indicators(df_raw)
        info = fetch_fundamentals(ticker)

        close = df["Close"].dropna()
        rsi = df["RSI"].dropna()
        if rsi.empty: continue

        rsi_last = float(rsi.iloc[-1])
        price_last = float(close.iloc[-1])
        ma20 = df["MA20"].dropna()
        ma200 = df["MA200"].dropna()

        # AT filters
        if not (rsi_min <= rsi_last <= rsi_max): continue
        if price_above_ma20 and not ma20.empty and price_last < ma20.iloc[-1]: continue
        if price_above_ma200 and not ma200.empty and price_last < ma200.iloc[-1]: continue

        # AF filters
        pe = info.get("trailingPE")
        dy = (info.get("dividendYield") or 0) * 100
        roe = (info.get("returnOnEquity") or 0) * 100

        if pe and pe > pe_max: continue
        if dy < dy_min: continue
        if roe < roe_min: continue

        # Framework scores
        scores = compute_all_scores(info, df)
        score_map = {s["name"]: s["score"] for s in scores}

        if score_map.get("Lynch", 0) < score_lynch_min: continue
        if score_map.get("Barsi", 0) < score_barsi_min: continue
        if score_map.get("Dalio", 0) < score_dalio_min: continue

        ret_1m = df["Return_1m"].dropna()
        ret_1m_val = float(ret_1m.iloc[-1]) if not ret_1m.empty else None
        vol = df["Volatility_30d"].dropna()
        vol_val = float(vol.iloc[-1]) if not vol.empty else None

        results.append({
            "Ticker": ticker,
            "Preço": price_last,
            "RSI": round(rsi_last, 1),
            "Ret. 1M (%)": round(ret_1m_val, 1) if ret_1m_val else None,
            "Vol. (%)": round(vol_val, 1) if vol_val else None,
            "P/L": round(pe, 1) if pe else None,
            "DY (%)": round(dy, 2),
            "ROE (%)": round(roe, 1),
            "Lynch": score_map.get("Lynch", 0),
            "Barsi": score_map.get("Barsi", 0),
            "Dalio": score_map.get("Dalio", 0),
            "Score Médio": round(sum(score_map.values()) / len(score_map), 0),
        })

    except Exception:
        continue

progress_bar.empty()
status_text.empty()

# ─── RESULTS ──────────────────────────────────────────────────────────────────
if not results:
    st.markdown("""
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:48px;text-align:center">
        <div style="font-family:'DM Serif Display',serif;font-size:24px;color:var(--muted)">Nenhuma ação passou pelos filtros</div>
        <div style="font-size:14px;color:var(--muted);margin-top:8px">Tente relaxar os critérios e rode novamente.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_results = pd.DataFrame(results).sort_values("Score Médio", ascending=False)

st.markdown(f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;color:var(--accent);margin-bottom:20px">{len(df_results)} ação(ões) passaram nos filtros</div>', unsafe_allow_html=True)

# Render table
def score_badge(v):
    if v is None: return "–"
    color = "#4af0c8" if v >= 65 else ("#f5c842" if v >= 40 else "#f05b5b")
    return f'<span style="font-family:\'DM Mono\',monospace;color:{color};font-size:12px">{int(v)}</span>'

def ret_cell(v):
    if v is None: return "–"
    color = "#4af0c8" if v >= 0 else "#f05b5b"
    sign = "+" if v >= 0 else ""
    return f'<span style="color:{color}">{sign}{v}%</span>'

rows_html = ""
for _, row in df_results.iterrows():
    pe_str = f"{row['P/L']:.1f}x" if row["P/L"] else "–"
    rows_html += f"""
    <tr>
        <td><strong style="color:var(--accent);font-family:'DM Mono',monospace">{row['Ticker']}</strong></td>
        <td>R$ {row['Preço']:.2f}</td>
        <td>{row['RSI']}</td>
        <td>{ret_cell(row['Ret. 1M (%)'])}</td>
        <td>{row['Vol. (%)'] or '–'}%</td>
        <td>{pe_str}</td>
        <td>{row['DY (%)']:.2f}%</td>
        <td>{row['ROE (%)']:.1f}%</td>
        <td>{score_badge(row['Lynch'])}</td>
        <td>{score_badge(row['Barsi'])}</td>
        <td>{score_badge(row['Dalio'])}</td>
        <td>{score_badge(row['Score Médio'])}</td>
    </tr>"""

st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow-x:auto">
<table class="data-table">
<thead><tr>
    <th>Ticker</th><th>Preço</th><th>RSI</th><th>1M</th><th>Vol.</th>
    <th>P/L</th><th>DY</th><th>ROE</th>
    <th>Lynch</th><th>Barsi</th><th>Dalio</th><th>Média</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer" style="margin-top:24px">
    O screener é uma ferramenta de filtragem quantitativa. Scores e indicadores são calculados com dados públicos disponíveis.
    Não constitui recomendação de compra ou venda de valores mobiliários.
</div>
""", unsafe_allow_html=True)
