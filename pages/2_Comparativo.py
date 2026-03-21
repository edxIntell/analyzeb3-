import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import STYLE, fetch_price_history, render_metric

st.set_page_config(page_title="Comparativo Multi-Asset · AnalyzeB3", page_icon="📊", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)

# ─── BENCHMARKS ──────────────────────────────────────────────────────────────
BENCHMARKS = {
    "CDI (aprox.)":     {"type": "fixed", "rate_annual": 0.105, "color": "#6b7080"},
    "IPCA+6%":          {"type": "fixed", "rate_annual": 0.165, "color": "#a89b6e"},
    "IBOV":             {"type": "ticker", "ticker": "^BVSP",   "color": "#4af0c8"},
    "Ouro (USD→BRL)":  {"type": "ticker", "ticker": "GLD",     "color": "#f5c842"},
    "S&P 500":          {"type": "ticker", "ticker": "^GSPC",   "color": "#7b6cf6"},
    "Dólar (BRL)":      {"type": "ticker", "ticker": "BRL=X",   "color": "#f05b5b"},
}

@st.cache_data(ttl=300)
def load_benchmark_series(period: str) -> dict:
    series = {}
    for name, cfg in BENCHMARKS.items():
        if cfg["type"] == "fixed":
            rate = cfg["rate_annual"]
            n = {"6mo": 126, "1y": 252, "2y": 504, "3y": 756}.get(period, 252)
            daily = (1 + rate) ** (1/252) - 1
            idx = pd.date_range(end=pd.Timestamp.today(), periods=n, freq="B")
            s = pd.Series([(1 + daily)**i for i in range(n)], index=idx)
            series[name] = s
        else:
            try:
                df = yf.download(cfg["ticker"], period=period, progress=False, threads=False, auto_adjust=True)
                if df is not None and not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    c = df["Close"].dropna()
                    if len(c) > 0:
                        series[name] = c / c.iloc[0]
            except Exception:
                pass
    return series

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:22px;margin-bottom:4px">AnalyzeB3</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#6b7080;letter-spacing:2px;text-transform:uppercase;margin-bottom:24px">Plataforma de análise</div>', unsafe_allow_html=True)

    ticker_input = st.text_input("Ação para comparar (ex: PETR4.SA)", value="BRKM5.SA").strip().upper()
    if not ticker_input.endswith(".SA"):
        ticker_input += ".SA"

    period = st.selectbox("Período", ["6mo", "1y", "2y", "3y"], index=1,
                          format_func=lambda x: {"6mo":"6 meses","1y":"1 ano","2y":"2 anos","3y":"3 anos"}[x])

    bench_sel = st.multiselect(
        "Benchmarks",
        list(BENCHMARKS.keys()),
        default=["CDI (aprox.)", "IBOV", "Ouro (USD→BRL)", "IPCA+6%"]
    )

    st.markdown("---")
    st.page_link("Home.py", label="Home")
    st.page_link("pages/1_Ficha_Ativo.py", label="Ficha de Ativo")
    st.page_link("pages/2_Comparativo.py", label="Comparativo Multi-Asset")
    st.page_link("pages/3_Screener.py", label="Screener")

# ─── LOAD ─────────────────────────────────────────────────────────────────────
with st.spinner("Carregando dados..."):
    df_acao = fetch_price_history(ticker_input, period)
    benchmarks = load_benchmark_series(period)

if df_acao.empty:
    st.error(f"Não foi possível carregar {ticker_input}")
    st.stop()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:32px">
    <div class="section-tag">COMPARATIVO MULTI-ASSET</div>
    <div class="section-title">{ticker_input} vs mercado</div>
</div>
""", unsafe_allow_html=True)

# ─── PERFORMANCE TABLE ────────────────────────────────────────────────────────
close_acao = df_acao["Close"].dropna()
ret_acao = (close_acao.iloc[-1] / close_acao.iloc[0] - 1) * 100

# Build comparison
rows = []
acao_ret = ret_acao
rows.append({
    "Ativo": ticker_input,
    "Retorno": acao_ret,
    "color": "#c8f564",
    "type": "acao"
})
for bname in bench_sel:
    if bname in benchmarks:
        s = benchmarks[bname]
        r = (s.iloc[-1] - 1) * 100
        rows.append({
            "Ativo": bname,
            "Retorno": r,
            "color": BENCHMARKS[bname]["color"],
            "type": "bench"
        })

rows.sort(key=lambda x: x["Retorno"], reverse=True)

# Metric summary row
st.markdown('<div class="section-tag">RETORNO NO PERÍODO</div>', unsafe_allow_html=True)
cols = st.columns(len(rows))
for i, row in enumerate(rows):
    v = row["Retorno"]
    cls = "up" if v >= 0 else "down"
    sign = "+" if v >= 0 else ""
    with cols[i]:
        st.markdown(render_metric(row["Ativo"], f"{sign}{v:.1f}%", delta_class=cls), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─── NORMALIZED PERFORMANCE CHART ────────────────────────────────────────────
st.markdown('<div class="section-tag">PERFORMANCE NORMALIZADA (base 100)</div>', unsafe_allow_html=True)

fig = go.Figure()

# Ação
norm_acao = close_acao / close_acao.iloc[0] * 100
fig.add_trace(go.Scatter(
    x=norm_acao.index, y=norm_acao,
    name=ticker_input,
    line=dict(color="#c8f564", width=2.5),
))

# Benchmarks
for bname in bench_sel:
    if bname in benchmarks:
        s = benchmarks[bname] * 100
        color = BENCHMARKS[bname]["color"]
        fig.add_trace(go.Scatter(
            x=s.index, y=s,
            name=bname,
            line=dict(color=color, width=1.5, dash="dot"),
            opacity=0.8
        ))

fig.add_hline(y=100, line_dash="dash", line_color="#242836", line_width=1)

fig.update_layout(
    height=450,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#13161e",
    font=dict(family="DM Sans, sans-serif", color="#6b7080", size=11),
    legend=dict(orientation="h", y=1.02, bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    yaxis=dict(ticksuffix="", gridcolor="#242836"),
    xaxis=dict(gridcolor="#242836"),
)
st.plotly_chart(fig, use_container_width=True)

# ─── RISK / RETURN SCATTER ────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-tag">RISCO × RETORNO</div>', unsafe_allow_html=True)

scatter_data = []
# Ação
daily_ret = close_acao.pct_change().dropna()
vol_a = daily_ret.std() * np.sqrt(252) * 100
scatter_data.append({"name": ticker_input, "vol": vol_a, "ret": acao_ret, "color": "#c8f564", "size": 18})

for bname in bench_sel:
    if bname not in benchmarks:
        continue
    s = benchmarks[bname]
    if BENCHMARKS[bname]["type"] == "fixed":
        vol_b = 0.5
    else:
        s_ret = s.pct_change().dropna()
        vol_b = s_ret.std() * np.sqrt(252) * 100
    r = (s.iloc[-1] - 1) * 100
    scatter_data.append({"name": bname, "vol": vol_b, "ret": r, "color": BENCHMARKS[bname]["color"], "size": 12})

fig_sc = go.Figure()
for d in scatter_data:
    fig_sc.add_trace(go.Scatter(
        x=[d["vol"]], y=[d["ret"]],
        mode="markers+text",
        marker=dict(color=d["color"], size=d["size"]),
        text=[d["name"]], textposition="top center",
        textfont=dict(color=d["color"], size=11),
        name=d["name"],
        showlegend=False,
    ))

fig_sc.add_hline(y=0, line_color="#242836", line_width=1)
fig_sc.update_layout(
    height=360,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#13161e",
    font=dict(family="DM Sans", color="#6b7080", size=11),
    xaxis=dict(title="Volatilidade anualizada (%)", gridcolor="#242836"),
    yaxis=dict(title=f"Retorno no período (%)", gridcolor="#242836"),
    margin=dict(l=0, r=0, t=20, b=0),
)
st.plotly_chart(fig_sc, use_container_width=True)

# ─── TABLE ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-tag">TABELA RESUMO</div>', unsafe_allow_html=True)

table_rows = ""
for d in sorted(scatter_data, key=lambda x: x["ret"], reverse=True):
    pos = "▲" if d["ret"] >= 0 else "▼"
    color = "#4af0c8" if d["ret"] >= 0 else "#f05b5b"
    rank = "⭐" if d["name"] == ticker_input else ""
    table_rows += f"""
    <tr>
        <td>{rank} {d['name']}</td>
        <td style="color:{color}">{pos} {d['ret']:+.1f}%</td>
        <td>{d['vol']:.1f}%</td>
        <td style="font-family:'DM Mono',monospace">{(d['ret']/d['vol']):.2f}x</td>
    </tr>"""

st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden">
<table class="data-table">
<thead><tr><th>Ativo</th><th>Retorno</th><th>Volatilidade</th><th>Ret/Risco</th></tr></thead>
<tbody>{table_rows}</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer" style="margin-top:24px">
    Retornos passados não garantem resultados futuros. CDI e IPCA+6% são aproximações para fins de comparação.
    Esta ferramenta não configura recomendação de investimento.
</div>
""", unsafe_allow_html=True)
