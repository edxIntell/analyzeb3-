import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import (
    STYLE, fetch_price_history, fetch_fundamentals,
    calc_all_indicators, compute_all_scores,
    render_metric, render_score_card, SAFE_TICKERS, compute_valuation
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
    st.markdown('<div style="font-size:11px;color:#6b7080">Navegação</div>', unsafe_allow_html=True)
    st.page_link("Home.py", label="Home")
    st.page_link("pages/1_Ficha_Ativo.py", label="Ficha de Ativo")
    st.page_link("pages/2_Comparativo.py", label="Comparativo Multi-Asset")
    st.page_link("pages/3_Screener.py", label="Screener")

# ─── LOAD DATA ────────────────────────────────────────────────────────────────
with st.spinner(f"Carregando {ticker_input}..."):
    df_raw = fetch_price_history(ticker_input, period)
    info = fetch_fundamentals(ticker_input)

if df_raw.empty:
    st.error(f"Não foi possível carregar dados para **{ticker_input}**. Verifique o ticker e tente novamente.")
    st.stop()

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
tab_at, tab_af, tab_vl, tab_fw = st.tabs(["ANÁLISE TÉCNICA", "ANÁLISE FUNDAMENTALISTA", "VALUATION", "FRAMEWORKS"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANÁLISE TÉCNICA
# ══════════════════════════════════════════════════════════════════════════════
with tab_at:
    # Quick metrics
    ret1m = df["Return_1m"].iloc[-1] if "Return_1m" in df.columns else None
    ret3m = df["Return_3m"].iloc[-1] if "Return_3m" in df.columns else None
    ret6m = df["Return_6m"].iloc[-1] if "Return_6m" in df.columns else None
    rsi_val = df["RSI"].iloc[-1] if "RSI" in df.columns else None
    vol_val = df["Volatility_30d"].iloc[-1] if "Volatility_30d" in df.columns else None

    c1, c2, c3, c4, c5 = st.columns(5)
    def fmt_ret(v):
        if v is None or np.isnan(v): return "–", "neutral"
        return f"{'+' if v>=0 else ''}{v:.1f}%", "up" if v>=0 else "down"

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
        if rsi_val and not np.isnan(rsi_val):
            rsi_cls = "down" if rsi_val > 70 else ("up" if rsi_val < 30 else "neutral")
            rsi_note = "sobrecomprado" if rsi_val > 70 else ("sobrevendido" if rsi_val < 30 else "neutro")
            st.markdown(render_metric("RSI (14)", f"{rsi_val:.1f}", rsi_note, rsi_cls), unsafe_allow_html=True)
        else:
            st.markdown(render_metric("RSI (14)", "–"), unsafe_allow_html=True)
    with c5:
        if vol_val and not np.isnan(vol_val):
            st.markdown(render_metric("Volatilidade", f"{vol_val:.1f}%", "anualizada", "neutral"), unsafe_allow_html=True)
        else:
            st.markdown(render_metric("Volatilidade", "–"), unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── MAIN CHART ──
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.02
    )

    # Candles
    if "Open" in df.columns and "High" in df.columns and "Low" in df.columns:
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Preço",
            increasing_line_color="#4af0c8", increasing_fillcolor="#4af0c8",
            decreasing_line_color="#f05b5b", decreasing_fillcolor="#f05b5b",
            line_width=1
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], line=dict(color="#4af0c8", width=1.5), name="Fechamento"), row=1, col=1)

    # Moving averages
    for col, color, name_ma in [("MA20","#f5c842","MM20"), ("MA50","#c8f564","MM50"), ("MA200","#7b6cf6","MM200")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color=color, width=1, dash="dot"),
                                      name=name_ma, opacity=0.8), row=1, col=1)

    # Bollinger
    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], line=dict(color="#6b7080", width=0.5, dash="dash"),
                                  name="BB Superior", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], line=dict(color="#6b7080", width=0.5, dash="dash"),
                                  name="BB Inferior", fill="tonexty", fillcolor="rgba(107,112,128,0.05)",
                                  showlegend=False), row=1, col=1)

    # Volume
    if "Volume" in df.columns:
        colors_v = ["#4af0c8" if df["Return_1d"].iloc[i] >= 0 else "#f05b5b" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors_v, opacity=0.7), row=2, col=1)

    # RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], line=dict(color="#c8f564", width=1.5), name="RSI"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#f05b5b", line_width=0.8, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#4af0c8", line_width=0.8, row=3, col=1)

    fig.update_layout(
        height=620,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#13161e",
        font=dict(family="DM Sans, sans-serif", color="#6b7080", size=11),
        legend=dict(orientation="h", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font_size=11),
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#242836", showgrid=True, row=i, col=1)
        fig.update_yaxes(gridcolor="#242836", showgrid=True, row=i, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # ── MACD chart ──
    if "MACD" in df.columns:
        st.markdown('<div class="section-tag">MACD</div>', unsafe_allow_html=True)
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df.index, y=df["MACD"], line=dict(color="#c8f564", width=1.5), name="MACD"))
        fig_macd.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], line=dict(color="#f5c842", width=1.5), name="Sinal"))
        hist_colors = ["#4af0c8" if v >= 0 else "#f05b5b" for v in df["MACD_Hist"].fillna(0)]
        fig_macd.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], marker_color=hist_colors, name="Histograma", opacity=0.8))
        fig_macd.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13161e",
                                font=dict(family="DM Sans", color="#6b7080", size=11),
                                legend=dict(orientation="h", bgcolor="rgba(0,0,0,0)"),
                                margin=dict(l=0, r=0, t=10, b=0))
        fig_macd.update_xaxes(gridcolor="#242836"); fig_macd.update_yaxes(gridcolor="#242836")
        st.plotly_chart(fig_macd, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANÁLISE FUNDAMENTALISTA
# ══════════════════════════════════════════════════════════════════════════════
with tab_af:
    if not info:
        st.warning("Dados fundamentalistas não disponíveis para este ticker.")
        st.stop()

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
