import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import utils as _utils_mod
importlib.reload(_utils_mod)
from utils import (
    STYLE, fetch_price_history, fetch_fundamentals,
    calc_all_indicators, compute_all_scores,
    render_metric, render_score_card, SAFE_TICKERS, compute_valuation,
    get_peers, fetch_peer_data
)
from ai_analysis import render_analysis_section

st.set_page_config(page_title="Ficha de Ativo · AnalyzeB3", page_icon="📊", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'DM Serif Display\',serif;font-size:22px;margin-bottom:4px">AnalyzeB3</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#6b7080;letter-spacing:2px;text-transform:uppercase;margin-bottom:24px">Plataforma de análise</div>', unsafe_allow_html=True)

    ticker_input = st.text_input("Ticker (ex: PETR4.SA)", value="BRKM5.SA").strip().upper()
    if not ticker_input.endswith(".SA"):
        ticker_input = ticker_input + ".SA"

    period = st.selectbox("Período", ["6mo", "1y", "2y", "3y"], index=1,
                          format_func=lambda x: {"6mo":"6 meses","1y":"1 ano","2y":"2 anos","3y":"3 anos"}[x])

    st.markdown("---")
    if st.button("🗑 Limpar cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#6b7080">Navegação</div>', unsafe_allow_html=True)
    st.page_link("Home.py", label="Home")
    st.page_link("pages/1_Ficha_Ativo.py", label="Ficha de Ativo")
    st.page_link("pages/2_Comparativo.py", label="Comparativo Multi-Asset")
    st.page_link("pages/3_Screener.py", label="Screener")

# ─── LOAD DATA ────────────────────────────────────────────────────────────────
# ── FETCH INLINE (evita cache de módulo) ─────────────────────────────────────
import requests as _rq
import pandas as _pd

def _load_prices(tkr, prd):
    sym   = tkr.upper().replace(".SA","")
    token = st.secrets.get("BRAPI_TOKEN","")
    rng   = {"6mo":"3mo","1y":"3mo","2y":"3mo","3y":"3mo"}.get(prd,"3mo")
    url   = f"https://brapi.dev/api/quote/{sym}"
    prm   = {"range": rng, "interval": "1d", "fundamental": "false"}
    if token:
        prm["token"] = token
    try:
        r    = _rq.get(url, params=prm, timeout=20)
        data = r.json()
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {data.get('message','')}"
        results = data.get("results",[])
        if not results:
            return None, f"sem results: {str(data)[:200]}"
        hist = results[0].get("historicalDataPrice") or []
        if not hist:
            return None, f"historicalDataPrice vazio. keys={list(results[0].keys())}"
        rows = []
        for h in hist:
            c = h.get("close") or h.get("adjustedClose")
            if c is None: continue
            try:
                d = (_pd.to_datetime(h["date"], unit="s")
                     if isinstance(h["date"],(int,float))
                     else _pd.to_datetime(h["date"]))
                rows.append({"Date":d,"Open":h.get("open") or c,
                             "High":h.get("high") or c,"Low":h.get("low") or c,
                             "Close":c,"Volume":h.get("volume") or 0})
            except: continue
        if not rows:
            return None, f"nenhuma row válida de {len(hist)} candles. ex={hist[0]}"
        df = _pd.DataFrame(rows).set_index("Date").sort_index()
        return df.dropna(subset=["Close"]), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

with st.spinner(f"Carregando {ticker_input}..."):
    df_raw, _err = _load_prices(ticker_input, period)
    if df_raw is None or df_raw.empty:
        st.error(f"Não foi possível carregar **{ticker_input}**")
        st.code(_err or "erro desconhecido")
        st.stop()
    info = fetch_fundamentals(ticker_input)

df = calc_all_indicators(df_raw)
close = df["Close"]
scores = compute_all_scores(info, df)
valuation = compute_valuation(info)

# ─── HEADER ───────────────────────────────────────────────────────────────────
name = info.get("longName") or info.get("shortName") or ticker_input
sector = info.get("sector", "")
industry = info.get("industry", "")
current_price = float(close.iloc[-1])
prev_price = float(close.iloc[-2]) if len(close) > 1 else current_price
change_pct = (current_price / prev_price - 1) * 100
change_class = "up" if change_pct >= 0 else "down"
change_sign = "+" if change_pct >= 0 else ""

st.markdown(f"""
<div style="margin-bottom:32px">
    <div style="font-family:'DM Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;margin-bottom:6px">
        {sector}{" · " + industry if industry else ""}
    </div>
    <div style="display:flex;align-items:baseline;gap:16px;flex-wrap:wrap">
        <h1 style="font-family:'DM Serif Display',serif;font-size:40px;font-weight:400;margin:0;color:var(--text)">{name}</h1>
        <span style="font-family:'DM Mono',monospace;font-size:16px;color:var(--muted)">{ticker_input}</span>
    </div>
    <div style="display:flex;align-items:baseline;gap:12px;margin-top:10px">
        <span style="font-family:'DM Serif Display',serif;font-size:36px;color:var(--text)">R$ {current_price:.2f}</span>
        <span style="font-family:'DM Mono',monospace;font-size:16px" class="{change_class}">{change_sign}{change_pct:.2f}% hoje</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_at, tab_af, tab_vl, tab_peers, tab_fw = st.tabs(["ANÁLISE TÉCNICA", "ANÁLISE FUNDAMENTALISTA", "VALUATION", "COMPARATIVO SETORIAL", "FRAMEWORKS"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANÁLISE TÉCNICA
# ══════════════════════════════════════════════════════════════════════════════
with tab_at:
    # ── CONTROLES DE TIMEFRAME E INDICADORES ──
    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])
    with ctrl1:
        timeframe = st.radio("Timeframe", ["Diário", "Semanal", "Mensal"],
                             horizontal=True, key="tf_radio")
    with ctrl2:
        chart_type = st.radio("Tipo", ["Candle", "Linha"], horizontal=True, key="ct_radio")
    with ctrl3:
        indicators = st.multiselect("Indicadores",
            ["MM20", "MM50", "MM200", "Bollinger", "VWAP"],
            default=["MM20", "MM50", "Bollinger"], key="ind_ms")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── RESAMPLE CONFORME TIMEFRAME ──
    def resample_ohlcv(df_in, tf):
        if tf == "Semanal":
            rule = "W"
        elif tf == "Mensal":
            rule = "ME"
        else:
            return df_in.copy()
        agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
        agg = {k: v for k, v in agg.items() if k in df_in.columns}
        return df_in.resample(rule).agg(agg).dropna(subset=["Close"])

    df_chart = resample_ohlcv(df, timeframe)
    df_chart = calc_all_indicators(df_chart)

    # ── MÉTRICAS ──
    def fmt_ret(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "–", "neutral"
        return f"{'+' if v>=0 else ''}{v:.1f}%", "up" if v>=0 else "down"

    ret1m  = float(df_chart["Return_1m"].dropna().iloc[-1])  if "Return_1m"  in df_chart.columns and len(df_chart["Return_1m"].dropna())  > 0 else None
    ret3m  = float(df_chart["Return_3m"].dropna().iloc[-1])  if "Return_3m"  in df_chart.columns and len(df_chart["Return_3m"].dropna())  > 0 else None
    ret6m  = float(df_chart["Return_6m"].dropna().iloc[-1])  if "Return_6m"  in df_chart.columns and len(df_chart["Return_6m"].dropna())  > 0 else None
    rsi_val= float(df_chart["RSI"].dropna().iloc[-1])        if "RSI"        in df_chart.columns and len(df_chart["RSI"].dropna())        > 0 else None
    vol_val= float(df_chart["Volatility_30d"].dropna().iloc[-1]) if "Volatility_30d" in df_chart.columns and len(df_chart["Volatility_30d"].dropna()) > 0 else None

    # Máxima e mínima do período visível
    price_max = float(df_chart["High"].max()) if "High" in df_chart.columns else float(df_chart["Close"].max())
    price_min = float(df_chart["Low"].min())  if "Low"  in df_chart.columns else float(df_chart["Close"].min())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        v, cls = fmt_ret(ret1m)
        st.markdown(render_metric("Retorno 1M", v, delta_class=cls), unsafe_allow_html=True)
    with c2:
        v, cls = fmt_ret(ret3m)
        st.markdown(render_metric("Retorno 3M", v, delta_class=cls), unsafe_allow_html=True)
    with c3:
        v, cls = fmt_ret(ret6m)
        st.markdown(render_metric("Retorno 6M", v, delta_class=cls), unsafe_allow_html=True)
    with c4:
        if rsi_val:
            rsi_cls  = "down" if rsi_val > 70 else ("up" if rsi_val < 30 else "neutral")
            rsi_note = "sobrecomprado" if rsi_val > 70 else ("sobrevendido" if rsi_val < 30 else "neutro")
            st.markdown(render_metric("RSI (14)", f"{rsi_val:.1f}", rsi_note, rsi_cls), unsafe_allow_html=True)
        else:
            st.markdown(render_metric("RSI (14)", "–"), unsafe_allow_html=True)
    with c5:
        st.markdown(render_metric("Máx período", f"R$ {price_max:.2f}"), unsafe_allow_html=True)
    with c6:
        st.markdown(render_metric("Mín período", f"R$ {price_min:.2f}"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── GRÁFICO PRINCIPAL ──
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.58, 0.18, 0.24],
        vertical_spacing=0.015,
        subplot_titles=("", "Volume", "RSI (14)"),
    )

    # Candles ou Linha
    if chart_type == "Candle" and all(c in df_chart.columns for c in ["Open","High","Low"]):
        fig.add_trace(go.Candlestick(
            x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
            low=df_chart["Low"], close=df_chart["Close"],
            name="Preço",
            increasing_line_color="#4af0c8", increasing_fillcolor="rgba(74,240,200,0.7)",
            decreasing_line_color="#f05b5b", decreasing_fillcolor="rgba(240,91,91,0.7)",
            line_width=1, whiskerwidth=0.8,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["Close"],
            line=dict(color="#4af0c8", width=2),
            fill="tozeroy", fillcolor="rgba(74,240,200,0.04)",
            name="Fechamento",
        ), row=1, col=1)

    # Médias móveis
    ma_cfg = {"MM20": ("MA20","#f5c842",1.2), "MM50": ("MA50","#c8f564",1.2), "MM200": ("MA200","#7b6cf6",1.5)}
    for ind_name, (col, color, width) in ma_cfg.items():
        if ind_name in indicators and col in df_chart.columns:
            s = df_chart[col].dropna()
            fig.add_trace(go.Scatter(
                x=s.index, y=s,
                line=dict(color=color, width=width),
                name=ind_name, opacity=0.9,
            ), row=1, col=1)

    # Bollinger
    if "Bollinger" in indicators and "BB_Upper" in df_chart.columns:
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["BB_Upper"],
            line=dict(color="rgba(107,112,128,0.6)", width=1, dash="dot"),
            name="BB+2σ", showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["BB_Lower"],
            line=dict(color="rgba(107,112,128,0.6)", width=1, dash="dot"),
            name="BB−2σ", fill="tonexty",
            fillcolor="rgba(107,112,128,0.06)",
            showlegend=True,
        ), row=1, col=1)
        # Linha central
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart["BB_Mid"],
            line=dict(color="rgba(107,112,128,0.35)", width=0.8),
            name="BB mid", showlegend=False,
        ), row=1, col=1)

    # VWAP (só no diário)
    if "VWAP" in indicators and timeframe == "Diário" and "Volume" in df_chart.columns:
        typical = (df_chart["High"] + df_chart["Low"] + df_chart["Close"]) / 3 if "High" in df_chart.columns else df_chart["Close"]
        cum_tp_vol = (typical * df_chart["Volume"]).cumsum()
        cum_vol    = df_chart["Volume"].cumsum()
        vwap = cum_tp_vol / cum_vol.replace(0, np.nan)
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=vwap,
            line=dict(color="#f0a84a", width=1.5, dash="dashdot"),
            name="VWAP",
        ), row=1, col=1)

    # Volume com cores
    if "Volume" in df_chart.columns:
        ret_col = df_chart["Close"].pct_change().fillna(0)
        vol_colors = ["rgba(74,240,200,0.6)" if r >= 0 else "rgba(240,91,91,0.6)" for r in ret_col]
        fig.add_trace(go.Bar(
            x=df_chart.index, y=df_chart["Volume"],
            name="Volume", marker_color=vol_colors,
            showlegend=False,
        ), row=2, col=1)
        # Média do volume
        vol_ma = df_chart["Volume"].rolling(20).mean()
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=vol_ma,
            line=dict(color="#f5c842", width=1),
            name="Vol MA20", showlegend=False,
        ), row=2, col=1)

    # RSI com zonas
    if "RSI" in df_chart.columns:
        rsi_s = df_chart["RSI"].dropna()
        fig.add_trace(go.Scatter(
            x=rsi_s.index, y=rsi_s,
            line=dict(color="#c8f564", width=1.5),
            name="RSI",
        ), row=3, col=1)
        # Zona sobrecomprada
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(240,91,91,0.07)",
                      line_width=0, row=3, col=1)
        # Zona sobrevendida
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(74,240,200,0.07)",
                      line_width=0, row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(240,91,91,0.5)", line_width=1, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="rgba(107,112,128,0.3)", line_width=0.8, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(74,240,200,0.5)", line_width=1, row=3, col=1)

    # Layout
    fig.update_layout(
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f1117",
        font=dict(family="DM Sans, sans-serif", color="#6b7080", size=11),
        legend=dict(
            orientation="h", y=1.02, x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            itemsizing="constant",
        ),
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=24, b=0),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1a1e28", font_size=12, font_family="DM Mono, monospace"),
    )

    # Eixos
    axis_style = dict(gridcolor="#1e2130", showgrid=True, zeroline=False,
                      tickfont=dict(size=10, color="#6b7080"))
    for i in range(1, 4):
        fig.update_xaxes(**axis_style, row=i, col=1,
                         showspikes=True, spikecolor="#4b5060",
                         spikethickness=1, spikedash="dot")
        fig.update_yaxes(**axis_style, row=i, col=1,
                         showspikes=True, spikecolor="#4b5060",
                         spikethickness=1, spikedash="dot")

    fig.update_yaxes(tickprefix="R$ ", row=1, col=1)
    fig.update_yaxes(title_text="Vol", title_font_size=10, row=2, col=1)
    fig.update_yaxes(title_text="RSI", title_font_size=10, range=[0,100], row=3, col=1)

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d","select2d","autoScale2d"],
        "displaylogo": False,
        "toImageButtonOptions": {"format": "png", "filename": f"{ticker_input}_chart", "scale": 2},
    })

    # ── MACD ──
    if "MACD" in df_chart.columns:
        st.markdown('<div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#c8f564;text-transform:uppercase;margin:4px 0 8px">MACD (12, 26, 9)</div>', unsafe_allow_html=True)
        fig_macd = make_subplots(rows=1, cols=1)
        macd_s = df_chart["MACD"].dropna()
        sig_s  = df_chart["MACD_Signal"].dropna()
        hist_s = df_chart["MACD_Hist"].dropna()
        hist_colors = ["rgba(74,240,200,0.7)" if v >= 0 else "rgba(240,91,91,0.7)" for v in hist_s]
        fig_macd.add_trace(go.Bar(x=hist_s.index, y=hist_s, marker_color=hist_colors,
                                   name="Histograma", showlegend=False))
        fig_macd.add_trace(go.Scatter(x=macd_s.index, y=macd_s,
                                       line=dict(color="#c8f564", width=1.5), name="MACD"))
        fig_macd.add_trace(go.Scatter(x=sig_s.index, y=sig_s,
                                       line=dict(color="#f5c842", width=1.5), name="Sinal"))
        fig_macd.add_hline(y=0, line_color="rgba(107,112,128,0.4)", line_width=0.8)
        fig_macd.update_layout(
            height=180, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0f1117",
            font=dict(family="DM Sans", color="#6b7080", size=11),
            legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)", font_size=11),
            margin=dict(l=0, r=0, t=4, b=0),
            hovermode="x unified",
        )
        fig_macd.update_xaxes(gridcolor="#1e2130", showspikes=True, spikecolor="#4b5060",
                               spikethickness=1, spikedash="dot")
        fig_macd.update_yaxes(gridcolor="#1e2130")
        st.plotly_chart(fig_macd, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANÁLISE FUNDAMENTALISTA
# ══════════════════════════════════════════════════════════════════════════════
with tab_af:
    if not info:
        st.warning("Dados fundamentalistas não disponíveis para este ticker via brapi.")

    def safe(key, fmt=None, mult=1):
        v = info.get(key)
        if v is None: return "–"
        try:
            v = float(v) * mult
            return fmt.format(v) if fmt else str(v)
        except: return "–"

    # Valuation
    st.markdown('<div class="section-tag">VALUATION</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(render_metric("P/L (trailing)", safe("trailingPE", "{:.1f}x")), unsafe_allow_html=True)
    with c2: st.markdown(render_metric("P/L (forward)", safe("forwardPE", "{:.1f}x")), unsafe_allow_html=True)
    with c3: st.markdown(render_metric("P/VP", safe("priceToBook", "{:.2f}x")), unsafe_allow_html=True)
    with c4: st.markdown(render_metric("EV/EBITDA", safe("enterpriseToEbitda", "{:.1f}x")), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(render_metric("P/Receita", safe("priceToSalesTrailing12Months", "{:.2f}x")), unsafe_allow_html=True)
    with c2: st.markdown(render_metric("EV/Receita", safe("enterpriseToRevenue", "{:.2f}x")), unsafe_allow_html=True)
    with c3:
        mc = info.get("marketCap")
        if mc:
            if mc >= 1e12: mc_str = f"R$ {mc/1e12:.1f}T"
            elif mc >= 1e9: mc_str = f"R$ {mc/1e9:.1f}B"
            else: mc_str = f"R$ {mc/1e6:.0f}M"
        else: mc_str = "–"
        st.markdown(render_metric("Market Cap", mc_str), unsafe_allow_html=True)
    with c4: st.markdown(render_metric("Beta", safe("beta", "{:.2f}")), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Rentabilidade
    st.markdown('<div class="section-tag">RENTABILIDADE</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(render_metric("ROE", safe("returnOnEquity", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c2: st.markdown(render_metric("ROA", safe("returnOnAssets", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c3: st.markdown(render_metric("Margem Bruta", safe("grossMargins", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c4: st.markdown(render_metric("Margem Líquida", safe("profitMargins", "{:.1f}%", 100)), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Dividendos
    st.markdown('<div class="section-tag">DIVIDENDOS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(render_metric("Dividend Yield", safe("dividendYield", "{:.2f}%", 100)), unsafe_allow_html=True)
    with c2: st.markdown(render_metric("Payout Ratio", safe("payoutRatio", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c3: st.markdown(render_metric("Div/Ação", safe("lastDividendValue", "R$ {:.2f}")), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # Crescimento & Endividamento
    st.markdown('<div class="section-tag">CRESCIMENTO E ENDIVIDAMENTO</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(render_metric("Cresc. Receita", safe("revenueGrowth", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c2: st.markdown(render_metric("Cresc. Lucro", safe("earningsGrowth", "{:.1f}%", 100)), unsafe_allow_html=True)
    with c3: st.markdown(render_metric("Dívida/PL", safe("debtToEquity", "{:.2f}x", 0.01)), unsafe_allow_html=True)
    with c4: st.markdown(render_metric("Current Ratio", safe("currentRatio", "{:.2f}x")), unsafe_allow_html=True)

    # Resumo descritivo
    summary = info.get("longBusinessSummary") or info.get("description")
    if summary:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-tag">SOBRE A EMPRESA</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:14px;color:var(--muted);line-height:1.7;max-width:800px">{summary[:800]}{"..." if len(summary)>800 else ""}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VALUATION
# ══════════════════════════════════════════════════════════════════════════════
with tab_vl:
    price = valuation["preco_atual"]
    consenso = valuation["consenso"]
    upside = valuation["upside_pct"]

    # Header consenso
    if consenso and price:
        upside_cls = "up" if upside >= 0 else "down"
        upside_sign = "+" if upside >= 0 else ""
        verdict = "SUBVALORIZADA" if upside >= 15 else ("SOBREVALORIZADA" if upside <= -15 else "PRÓXIMA DO JUSTO")
        verdict_color = "#4af0c8" if upside >= 15 else ("#f05b5b" if upside <= -15 else "#f5c842")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(render_metric("Preço atual", f"R$ {float(price):.2f}"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_metric("Preço justo (consenso)", f"R$ {consenso:.2f}", delta_class=upside_cls), unsafe_allow_html=True)
        with c3:
            st.markdown(render_metric("Upside/Downside", f"{upside_sign}{upside:.1f}%", verdict, upside_cls), unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#13161e;border:1px solid #242836;border-left:4px solid {verdict_color};
             border-radius:0 10px 10px 0;padding:16px 20px;margin:16px 0 28px">
            <span style="font-size:11px;letter-spacing:2px;color:#6b7080;font-family:monospace">VEREDICTO DO CONSENSO</span>
            <div style="font-size:22px;font-weight:500;color:{verdict_color};margin-top:4px">{verdict}</div>
            <div style="font-size:12px;color:#6b7080;margin-top:4px">
                Média de {valuation["validos"]} modelo(s) com dados suficientes
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Dados fundamentalistas insuficientes para calcular valuation. Tente um ticker com mais cobertura (ex: PETR4, VALE3, ITUB4).")

    # Modelos individuais
    st.markdown('<div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:#c8f564;text-transform:uppercase;margin-bottom:16px">MODELOS DE VALUATION</div>', unsafe_allow_html=True)

    for m in valuation["modelos"]:
        if m["valido"] and m["valor"]:
            val = m["valor"]
            price_f = float(price) if price else 0
            diff = ((val / price_f) - 1) * 100 if price_f > 0 else 0
            diff_color = "#4af0c8" if diff >= 0 else "#f05b5b"
            diff_sign = "+" if diff >= 0 else ""

            inputs_html = " · ".join(f'<span style="color:#6b7080">{k}:</span> <span style="color:#e8eaf2">{v}</span>' for k, v in m.get("inputs", {}).items())

            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #242836;border-radius:10px;padding:20px 24px;margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
                    <div>
                        <div style="font-size:16px;font-weight:500;color:#e8eaf2">{m["modelo"]}</div>
                        <div style="font-size:11px;color:#6b7080;margin-top:3px;font-family:monospace">{m["formula"]}</div>
                        <div style="font-size:11px;margin-top:6px;font-family:monospace">{inputs_html}</div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:26px;font-weight:500;color:#e8eaf2">R$ {val:.2f}</div>
                        <div style="font-size:13px;color:{diff_color};font-family:monospace">{diff_sign}{diff:.1f}% vs atual</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#13161e;border:1px solid #242836;border-radius:10px;padding:16px 24px;margin-bottom:10px;opacity:0.5">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <div style="font-size:15px;color:#6b7080">{m["modelo"]}</div>
                        <div style="font-size:11px;color:#3d4050;margin-top:3px">{m.get("motivo","dados insuficientes")}</div>
                    </div>
                    <div style="font-family:monospace;font-size:13px;color:#3d4050">N/D</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1a1710;border:1px solid #3d3520;border-left:3px solid #f5c842;border-radius:0 8px 8px 0;
         padding:14px 18px;font-size:12px;color:#a89b6e;line-height:1.6;margin-top:20px">
        <strong style="color:#f5c842">Sobre os modelos:</strong>
        Graham e Bazin são métodos clássicos conservadores. Gordon/DDM é indicado para empresas pagadoras de dividendos.
        DCF e EV/EBITDA dependem de dados de fluxo de caixa e dívida. O consenso é a média simples dos modelos com dados disponíveis.
        Valuation é uma estimativa — não uma certeza. Use como referência comparativa, não como alvo absoluto.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPARATIVO SETORIAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_peers:
    sector = info.get("sector", "")
    peers = get_peers(ticker_input, sector)
    all_peers_br  = [t for t in peers.get("br", [])  if t != ticker_input]
    all_peers_intl = peers.get("intl", [])

    st.markdown(f'''
    <div style="margin-bottom:20px">
        <div style="font-family:monospace;font-size:10px;letter-spacing:3px;color:#c8f564;text-transform:uppercase;margin-bottom:6px">
            COMPARATIVO SETORIAL · {sector or "Setor"}
        </div>
        <div style="font-size:13px;color:#6b7080">
            {len(all_peers_br)} pares brasileiros · {len(all_peers_intl)} pares internacionais
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        sel_br = st.multiselect("Pares brasileiros", all_peers_br, default=all_peers_br[:4])
    with col_sel2:
        sel_intl = st.multiselect("Pares internacionais", all_peers_intl, default=all_peers_intl[:4])

    if st.button("Carregar comparativo", key="btn_peers"):
        tickers_to_fetch = [ticker_input] + sel_br + sel_intl
        with st.spinner(f"Buscando dados de {len(tickers_to_fetch)} empresas..."):
            peers_data = fetch_peer_data(tickers_to_fetch)
        st.session_state["peers_data"] = peers_data
        st.session_state["peers_ticker"] = ticker_input

    if st.session_state.get("peers_data") and st.session_state.get("peers_ticker") == ticker_input:
        peers_data = st.session_state["peers_data"]

        # ── PERFORMANCE 1 ANO ──
        st.markdown('<div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#c8f564;text-transform:uppercase;margin:20px 0 12px">RETORNO 1 ANO</div>', unsafe_allow_html=True)
        perf_data = [(d["ticker"], d.get("ret_1a"), d["is_br"]) for d in peers_data if d.get("ret_1a") is not None]
        perf_data.sort(key=lambda x: x[1], reverse=True)
        if perf_data:
            fig_bar = go.Figure()
            colors = ["#c8f564" if t == ticker_input else ("#4af0c8" if br else "#7b6cf6") for t, _, br in perf_data]
            fig_bar.add_trace(go.Bar(
                x=[t.replace(".SA","") for t, _, _ in perf_data],
                y=[v for _, v, _ in perf_data],
                marker_color=colors,
                text=[f"{v:+.1f}%" for _, v, _ in perf_data],
                textposition="outside",
            ))
            fig_bar.add_hline(y=0, line_color="#242836", line_width=1)
            fig_bar.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13161e",
                font=dict(family="DM Sans", color="#6b7080", size=11),
                margin=dict(l=0,r=0,t=20,b=0), showlegend=False,
                yaxis=dict(gridcolor="#242836", ticksuffix="%"),
                xaxis=dict(gridcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── TABELA COMPARATIVA ──
        st.markdown('<div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#c8f564;text-transform:uppercase;margin:20px 0 12px">MÚLTIPLOS COMPARATIVOS</div>', unsafe_allow_html=True)

        def fmt_val(v, suffix="", mult=1, decimals=1):
            if v is None: return "–"
            try: return f"{float(v)*mult:.{decimals}f}{suffix}"
            except: return "–"

        def mc_fmt(v):
            if v is None: return "–"
            v = float(v)
            if v >= 1e12: return f"{v/1e12:.1f}T"
            if v >= 1e9:  return f"{v/1e9:.1f}B"
            if v >= 1e6:  return f"{v/1e6:.0f}M"
            return str(v)

        rows_html = ""
        for d in peers_data:
            is_main = d["ticker"] == ticker_input
            flag = "🇧🇷" if d["is_br"] else "🌎"
            highlight = "border-left:3px solid #c8f564;" if is_main else ""
            name_short = (d["nome"] or d["ticker"])[:22]
            moeda = d.get("moeda","")
            dy_val = d.get("dy")
            dy_str = f"{float(dy_val)*100:.1f}%" if dy_val else "–"
            roe_val = d.get("roe")
            roe_str = f"{float(roe_val)*100:.1f}%" if roe_val else "–"
            mg_val = d.get("margem")
            mg_str = f"{float(mg_val)*100:.1f}%" if mg_val else "–"
            ret_val = d.get("ret_1a")
            ret_str = f"{ret_val:+.1f}%" if ret_val is not None else "–"
            ret_color = "#4af0c8" if (ret_val or 0) >= 0 else "#f05b5b"

            rows_html += f"""<tr style="{highlight}">
                <td><strong style="color:{'#c8f564' if is_main else '#e8eaf2'}">{flag} {d['ticker'].replace('.SA','')}</strong>
                    <div style="font-size:11px;color:#6b7080">{name_short}</div></td>
                <td style="font-family:monospace">{moeda} {fmt_val(d.get('preco'), decimals=2)}</td>
                <td style="font-family:monospace">{fmt_val(d.get('pl'), 'x')}</td>
                <td style="font-family:monospace">{fmt_val(d.get('pvp'), 'x')}</td>
                <td style="font-family:monospace">{fmt_val(d.get('ev_ebitda'), 'x')}</td>
                <td style="font-family:monospace;color:#4af0c8">{dy_str}</td>
                <td style="font-family:monospace">{roe_str}</td>
                <td style="font-family:monospace">{mg_str}</td>
                <td style="font-family:monospace;color:{ret_color}">{ret_str}</td>
                <td style="font-family:monospace">{mc_fmt(d.get('market_cap'))}</td>
            </tr>"""

        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid #242836;border-radius:10px;overflow-x:auto">
        <table class="data-table" style="min-width:780px">
        <thead><tr>
            <th>Empresa</th><th>Preço</th><th>P/L</th><th>P/VP</th><th>EV/EBITDA</th>
            <th>DY</th><th>ROE</th><th>Margem</th><th>Ret. 1A</th><th>Mkt Cap</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
        </table></div>
        """, unsafe_allow_html=True)

        # ── SCATTER P/L vs ROE ──
        st.markdown('<div style="font-family:monospace;font-size:10px;letter-spacing:2px;color:#c8f564;text-transform:uppercase;margin:24px 0 12px">P/L × ROE — POSICIONAMENTO RELATIVO</div>', unsafe_allow_html=True)
        fig_sc = go.Figure()
        for d in peers_data:
            pl = d.get("pl")
            roe = d.get("roe")
            if pl and roe:
                is_main = d["ticker"] == ticker_input
                color = "#c8f564" if is_main else ("#4af0c8" if d["is_br"] else "#7b6cf6")
                size = 18 if is_main else 10
                label = d["ticker"].replace(".SA","")
                fig_sc.add_trace(go.Scatter(
                    x=[float(roe)*100], y=[float(pl)],
                    mode="markers+text",
                    marker=dict(color=color, size=size),
                    text=[label], textposition="top center",
                    textfont=dict(color=color, size=10),
                    name=label, showlegend=False,
                ))
        fig_sc.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13161e",
            font=dict(family="DM Sans", color="#6b7080", size=11),
            xaxis=dict(title="ROE (%)", gridcolor="#242836"),
            yaxis=dict(title="P/L (x)", gridcolor="#242836"),
            margin=dict(l=0,r=0,t=20,b=0))

        # legenda manual
        leg_html = '''<div style="display:flex;gap:20px;font-size:12px;color:#6b7080;margin-top:8px">
            <span><span style="color:#c8f564">■</span> Ativo selecionado</span>
            <span><span style="color:#4af0c8">■</span> Pares BR</span>
            <span><span style="color:#7b6cf6">■</span> Pares internacionais</span>
        </div>'''
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown(leg_html, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1a1710;border:1px solid #3d3520;border-left:3px solid #f5c842;
             border-radius:0 8px 8px 0;padding:14px 18px;font-size:12px;color:#a89b6e;
             line-height:1.6;margin-top:20px">
            Dados coletados via Yahoo Finance. Empresas internacionais em USD. 
            Retorno 1A sem ajuste cambial. Não constitui recomendação de investimento.
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FRAMEWORKS
# ══════════════════════════════════════════════════════════════════════════════
with tab_fw:
    st.markdown(f"""
    <div class="section-tag">DASHBOARD COMPARATIVO DE FRAMEWORKS</div>
    <div class="section-title">{name}</div>
    """, unsafe_allow_html=True)

    # Radar chart dos scores
    labels = [s["name"] for s in scores]
    vals = [s["score"] for s in scores]
    colors = [s["color"] for s in scores]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(200,245,100,0.08)",
        line=dict(color="#c8f564", width=2),
        name="Score"
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="#13161e",
            radialaxis=dict(visible=True, range=[0,100], gridcolor="#242836", tickfont=dict(color="#6b7080", size=10)),
            angularaxis=dict(gridcolor="#242836", tickfont=dict(family="DM Serif Display", color="#e8eaf2", size=14)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=320,
        margin=dict(l=60, r=60, t=30, b=30),
    )

    col_radar, col_desc = st.columns([1, 2])
    with col_radar:
        st.plotly_chart(fig_radar, use_container_width=True)
        # Score total
        avg_score = sum(vals) / len(vals)
        avg_color = "#4af0c8" if avg_score >= 65 else ("#f5c842" if avg_score >= 40 else "#f05b5b")
        st.markdown(f"""
        <div style="text-align:center;margin-top:-8px">
            <div style="font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);letter-spacing:2px">SCORE MÉDIO</div>
            <div style="font-family:'DM Serif Display',serif;font-size:52px;color:{avg_color};line-height:1">{avg_score:.0f}</div>
            <div style="font-size:12px;color:var(--muted)">/100</div>
        </div>
        """, unsafe_allow_html=True)

    with col_desc:
        for s in scores:
            score = s["score"]
            color = s["color"]
            badge_color = "#4af0c8" if score >= 65 else ("#f5c842" if score >= 40 else "#f05b5b")
            criteria_rows = ""
            for c in s["criteria"]:
                icon = "✓" if c["pass"] is True else ("✗" if c["pass"] is False else "–")
                ccolor = "#4af0c8" if c["pass"] is True else ("#f05b5b" if c["pass"] is False else "#6b7080")
                criteria_rows += f'''<div style="display:flex;justify-content:space-between;font-size:12px;padding:5px 0;border-bottom:1px solid #242836;color:#6b7080">
                    <span>{c["label"]}</span>
                    <span style="font-family:monospace;color:{ccolor}">{icon} {c["note"]}</span>
                </div>'''
            html = f'''<div style="background:#13161e;border:1px solid #242836;border-radius:10px;padding:20px;margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                    <div>
                        <div style="font-size:18px;color:#e8eaf2;font-weight:500">{s["name"]}</div>
                        <div style="font-size:11px;color:#6b7080;margin-top:2px">{s["description"]}</div>
                    </div>
                    <div style="font-size:26px;font-weight:500;color:{badge_color}">{score}<span style="font-size:13px;color:#6b7080">/100</span></div>
                </div>
                <div style="background:#1a1e28;border-radius:3px;height:5px;margin:10px 0 14px">
                    <div style="width:{score}%;height:5px;border-radius:3px;background:{color}"></div>
                </div>
                {criteria_rows}
            </div>'''
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer" style="margin-top:24px">
        Os scores são calculados automaticamente com base em critérios públicos atribuídos a cada metodologia de investimento.
        Não representam recomendação de compra ou venda. Um score alto indica que o ativo atende aos critérios do framework,
        não que o investimento é adequado para o seu perfil.
    </div>
    """, unsafe_allow_html=True)

# ── ANÁLISE IA ──────────────────────────────────────────────────────────
st.markdown('<div style="margin-top:40px"><hr style="border-color:var(--border);margin-bottom:0"></div>', unsafe_allow_html=True)
render_analysis_section(ticker_input, name, info, df, scores)
