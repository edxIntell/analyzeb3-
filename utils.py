import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg: #0d0f14;
    --surface: #13161e;
    --surface2: #1a1e28;
    --border: #242836;
    --accent: #c8f564;
    --accent2: #4af0c8;
    --accent3: #f5c842;
    --text: #e8eaf2;
    --muted: #6b7080;
    --danger: #f05b5b;
    --up: #4af0c8;
    --down: #f05b5b;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background-color: var(--bg) !important; }
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Metric cards */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    font-weight: 400;
    color: var(--text);
    line-height: 1;
}
.metric-delta {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    margin-top: 6px;
}
.up { color: var(--up); }
.down { color: var(--down); }
.neutral { color: var(--muted); }

/* Score cards */
.score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 12px;
}
.score-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.score-name {
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: var(--text);
}
.score-badge {
    font-family: 'DM Mono', monospace;
    font-size: 22px;
    font-weight: 500;
}
.score-bar-bg {
    background: var(--surface2);
    border-radius: 3px;
    height: 6px;
    margin: 8px 0 16px;
    overflow: hidden;
}
.score-bar-fill {
    height: 6px;
    border-radius: 3px;
    transition: width 0.6s ease;
}
.score-criterion {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    color: var(--muted);
}
.score-criterion:last-child { border-bottom: none; }
.score-criterion span:last-child { font-family: 'DM Mono', monospace; font-size: 12px; }
.pass { color: var(--accent2); }
.fail { color: var(--danger); }
.warn { color: var(--accent3); }

/* Section headers */
.section-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 6px;
}
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    font-weight: 400;
    color: var(--text);
    margin: 0 0 24px;
}

/* Table styling */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.data-table th {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    color: var(--muted);
    text-transform: uppercase;
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.data-table td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    font-family: 'DM Mono', monospace;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface2); }

/* Disclaimer */
.disclaimer {
    background: #1a1710;
    border: 1px solid #3d3520;
    border-left: 3px solid var(--accent3);
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 12px;
    color: #a89b6e;
    line-height: 1.6;
}

/* Streamlit overrides */
div[data-testid="stSelectbox"] > div,
div[data-testid="stTextInput"] > div > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    border-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }
</style>
"""

# ─── DATA FETCHING ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    # Remove .SA suffix for brapi
    symbol = ticker.replace(".SA", "")
    period_map = {"6mo": "6mo", "1y": "1y", "2y": "2y", "3y": "3y"}
    range_param = period_map.get(period, "1y")

    # Try brapi.dev first
    try:
        url = f"{BRAPI_BASE}/quote/{symbol}?range={range_param}&interval=1d&fundamental=false"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        results = data.get("results", [])
        if results:
            r = results[0]
            hist = r.get("historicalDataPrice") or []
            # Also try to get current price if history is short
            rows = []
            for h in hist:
                close_val = h.get("close") or h.get("adjustedClose")
                if close_val is not None:
                    try:
                        date_val = pd.to_datetime(h["date"], unit="s") if isinstance(h["date"], (int, float)) else pd.to_datetime(h["date"])
                        rows.append({
                            "Date":   date_val,
                            "Open":   h.get("open") or close_val,
                            "High":   h.get("high") or close_val,
                            "Low":    h.get("low") or close_val,
                            "Close":  close_val,
                            "Volume": h.get("volume") or 0,
                        })
                    except Exception:
                        continue
            if rows:
                df = pd.DataFrame(rows).set_index("Date").sort_index()
                df = df.dropna(subset=["Close"])
                return df
    except Exception:
        pass

    # Fallback: yfinance
    try:
        import yfinance as yf
        df = yf.download(ticker, period=period, progress=False, threads=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(c) for c in df.columns]
            df = df.dropna(subset=["Close"])
            return df
    except Exception:
        pass

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_fundamentals(ticker: str) -> dict:
    symbol = ticker.replace(".SA", "")

    # Try brapi fundamentals
    try:
        url = f"{BRAPI_BASE}/quote/{symbol}?fundamental=true"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        results = data.get("results", [])
        if results:
            r = results[0]
            info = {}
            # Map brapi fields to yfinance-style keys
            info["longName"]              = r.get("longName") or r.get("shortName", symbol)
            info["shortName"]             = r.get("shortName", symbol)
            info["sector"]                = r.get("sector", "")
            info["industry"]              = r.get("industry", "")
            info["marketCap"]             = r.get("marketCap")
            info["trailingPE"]            = r.get("trailingPE")
            info["forwardPE"]             = r.get("forwardPE")
            info["priceToBook"]           = r.get("priceToBook")
            info["enterpriseToEbitda"]    = r.get("enterpriseToEbitda")
            info["enterpriseToRevenue"]   = r.get("enterpriseToRevenue")
            info["returnOnEquity"]        = r.get("returnOnEquity")
            info["returnOnAssets"]        = r.get("returnOnAssets")
            info["profitMargins"]         = r.get("profitMargins")
            info["grossMargins"]          = r.get("grossMargins")
            info["dividendYield"]         = r.get("dividendYield")
            info["payoutRatio"]           = r.get("payoutRatio")
            info["debtToEquity"]          = r.get("debtToEquity")
            info["revenueGrowth"]         = r.get("revenueGrowth")
            info["earningsGrowth"]        = r.get("earningsGrowth")
            info["beta"]                  = r.get("beta")
            info["currentRatio"]          = r.get("currentRatio")
            info["lastDividendValue"]     = r.get("dividendsPerShare")
            info["longBusinessSummary"]   = r.get("longBusinessSummary", "")
            info["priceToSalesTrailing12Months"] = r.get("priceToSalesTrailing12Months")
            # Remove None values to avoid downstream issues
            info = {k: v for k, v in info.items() if v is not None}
            return info
    except Exception:
        pass

    # Fallback: yfinance
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        return t.info or {}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def fetch_benchmark_returns(period: str = "1y") -> dict:
    benchmarks = {
        "IBOV":    ("^BVSP", "yf"),
        "Ouro":    ("GLD",   "yf"),
        "S&P500":  ("^GSPC", "yf"),
        "Dólar":   ("BRL=X", "yf"),
    }
    results = {}
    for name, (sym, src) in benchmarks.items():
        try:
            import yfinance as yf
            df = yf.download(sym, period=period, progress=False, threads=False, auto_adjust=True)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                close = df["Close"].dropna()
                if len(close) >= 2:
                    results[name] = float((close.iloc[-1] / close.iloc[0] - 1) * 100)
        except Exception:
            pass
    return results


# ─── TECHNICAL INDICATORS ──────────────────────────────────────────────────────

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calc_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    mid = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    upper = mid + std * sigma
    lower = mid - std * sigma
    return upper, mid, lower

def calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    df = df.copy()
    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()
    df["RSI"] = calc_rsi(close)
    df["MACD"], df["MACD_Signal"], df["MACD_Hist"] = calc_macd(close)
    df["BB_Upper"], df["BB_Mid"], df["BB_Lower"] = calc_bollinger(close)
    df["Return_1d"] = close.pct_change() * 100
    df["Return_1m"] = close.pct_change(21) * 100
    df["Return_3m"] = close.pct_change(63) * 100
    df["Return_6m"] = close.pct_change(126) * 100
    df["Return_1y"] = close.pct_change(252) * 100
    df["Volatility_30d"] = df["Return_1d"].rolling(30).std() * np.sqrt(252)
    return df


# ─── FRAMEWORK SCORES ──────────────────────────────────────────────────────────

def score_lynch(info: dict, df: pd.DataFrame) -> dict:
    criteria = []
    score = 0

    pe = info.get("trailingPE") or info.get("forwardPE")
    eps_growth = info.get("earningsGrowth") or info.get("revenueGrowth")

    # PEG ratio
    if pe and eps_growth and eps_growth > 0:
        peg = pe / (eps_growth * 100)
        pass_peg = peg < 1.0
        criteria.append({"label": f"PEG Ratio ({peg:.2f})", "pass": pass_peg,
                          "note": "< 1.0 ideal" if not pass_peg else "✓ atrativo"})
        if pass_peg: score += 30
    else:
        criteria.append({"label": "PEG Ratio", "pass": None, "note": "dados insuficientes"})

    # Earnings growth
    if eps_growth:
        g = eps_growth * 100
        pass_g = g > 15
        criteria.append({"label": f"Crescimento lucro ({g:.1f}% a.a.)", "pass": pass_g,
                          "note": "> 15% a.a." if not pass_g else "✓ forte"})
        if pass_g: score += 25
        elif g > 0: score += 10
    else:
        criteria.append({"label": "Crescimento lucro", "pass": None, "note": "dados insuficientes"})

    # P/L razoável
    if pe:
        pass_pe = 5 < pe < 30
        criteria.append({"label": f"P/L ({pe:.1f}x)", "pass": pass_pe,
                          "note": "entre 5x e 30x" if not pass_pe else "✓ razoável"})
        if pass_pe: score += 20

    # Dívida/Patrimônio
    debt_equity = info.get("debtToEquity")
    if debt_equity:
        de = debt_equity / 100
        pass_de = de < 0.5
        criteria.append({"label": f"Dívida/PL ({de:.2f}x)", "pass": pass_de,
                          "note": "< 0.5x" if not pass_de else "✓ saudável"})
        if pass_de: score += 25

    return {"name": "Lynch", "score": min(score, 100), "color": "#4af0c8", "criteria": criteria,
            "description": "Crescimento + PEG + tipo de empresa"}


def score_barsi(info: dict, df: pd.DataFrame) -> dict:
    criteria = []
    score = 0

    # Dividend yield
    dy = info.get("dividendYield")
    if dy:
        dy_pct = dy * 100
        # CDI aproximado 10.5%
        pass_dy = dy_pct > 6.0
        criteria.append({"label": f"Dividend Yield ({dy_pct:.2f}%)", "pass": pass_dy,
                          "note": "< 6% a.a." if not pass_dy else "✓ acima da meta"})
        if dy_pct > 10: score += 35
        elif dy_pct > 6: score += 25
        elif dy_pct > 3: score += 10

    # Payout consistente
    payout = info.get("payoutRatio")
    if payout:
        p = payout * 100
        pass_p = 30 <= p <= 80
        criteria.append({"label": f"Payout ratio ({p:.0f}%)", "pass": pass_p,
                          "note": "ideal entre 30-80%" if not pass_p else "✓ sustentável"})
        if pass_p: score += 25

    # ROE
    roe = info.get("returnOnEquity")
    if roe:
        roe_pct = roe * 100
        pass_roe = roe_pct > 12
        criteria.append({"label": f"ROE ({roe_pct:.1f}%)", "pass": pass_roe,
                          "note": "< 12%" if not pass_roe else "✓ rentável"})
        if pass_roe: score += 20

    # Setor defensivo
    sector = info.get("sector", "")
    defensive = any(s in sector.lower() for s in ["utilities", "financial", "energy", "consumer staples"])
    criteria.append({"label": f"Setor defensivo ({sector or 'N/D'})", "pass": defensive,
                      "note": "✓ defensivo" if defensive else "setor cíclico"})
    if defensive: score += 20

    return {"name": "Barsi", "score": min(score, 100), "color": "#f5c842", "criteria": criteria,
            "description": "Dividendos + Yield + Setores defensivos"}


def score_dalio(info: dict, df: pd.DataFrame) -> dict:
    criteria = []
    score = 0

    if df.empty or len(df) < 60:
        return {"name": "Dalio", "score": 0, "color": "#c8f564", "criteria": [
            {"label": "Dados insuficientes", "pass": None, "note": "mínimo 60 pregões"}
        ], "description": "Macro + Paridade de risco"}

    close = df["Close"]
    returns = close.pct_change().dropna()

    # Volatilidade anualizada
    vol = returns.std() * np.sqrt(252) * 100
    pass_vol = vol < 30
    criteria.append({"label": f"Volatilidade ({vol:.1f}% a.a.)", "pass": pass_vol,
                      "note": "< 30% a.a." if not pass_vol else "✓ controlada"})
    if pass_vol: score += 25

    # Sharpe simplificado (vs CDI 10.5%)
    cdi_daily = 0.105 / 252
    excess = returns.mean() - cdi_daily
    sharpe = (excess / returns.std()) * np.sqrt(252)
    pass_sharpe = sharpe > 0.5
    criteria.append({"label": f"Sharpe approx. ({sharpe:.2f})", "pass": pass_sharpe,
                      "note": "< 0.5" if not pass_sharpe else "✓ bom risco/retorno"})
    if sharpe > 1.0: score += 30
    elif pass_sharpe: score += 20

    # Max drawdown 1 ano
    rolling_max = close.rolling(252, min_periods=1).max()
    drawdown = (close - rolling_max) / rolling_max * 100
    max_dd = drawdown.min()
    pass_dd = max_dd > -30
    criteria.append({"label": f"Max drawdown ({max_dd:.1f}%)", "pass": pass_dd,
                      "note": "drawdown severo" if not pass_dd else "✓ tolerável"})
    if pass_dd: score += 25

    # Beta implícito (vs IBOV)
    try:
        ibov = yf.download("^BVSP", period="1y", progress=False, threads=False, auto_adjust=True)
        if ibov is not None and not ibov.empty:
            if isinstance(ibov.columns, pd.MultiIndex):
                ibov.columns = ibov.columns.get_level_values(0)
            ibov_ret = ibov["Close"].pct_change().dropna()
            common = returns.index.intersection(ibov_ret.index)
            if len(common) > 30:
                cov = np.cov(returns.loc[common], ibov_ret.loc[common])[0][1]
                var_ibov = ibov_ret.loc[common].var()
                beta = cov / var_ibov if var_ibov > 0 else None
                if beta:
                    pass_beta = 0.5 < beta < 1.5
                    criteria.append({"label": f"Beta ({beta:.2f})", "pass": pass_beta,
                                      "note": "alta correlação" if not pass_beta else "✓ balanceado"})
                    if pass_beta: score += 20
    except Exception:
        criteria.append({"label": "Beta", "pass": None, "note": "não calculado"})

    return {"name": "Dalio", "score": min(score, 100), "color": "#c8f564", "criteria": criteria,
            "description": "Macro + Volatilidade + Risco/retorno"}


def compute_all_scores(info: dict, df: pd.DataFrame) -> list:
    return [
        score_lynch(info, df),
        score_barsi(info, df),
        score_dalio(info, df),
    ]


# ─── RENDERING HELPERS ─────────────────────────────────────────────────────────

def render_metric(label: str, value: str, delta: str = "", delta_class: str = "neutral"):
    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def render_score_card(s: dict):
    score = s["score"]
    color = s["color"]
    if score >= 65:
        badge_class = "up"
    elif score >= 40:
        badge_class = "warn"
    else:
        badge_class = "down"

    criteria_html = ""
    for c in s["criteria"]:
        if c["pass"] is True:
            cls = "pass"
            icon = "✓"
        elif c["pass"] is False:
            cls = "fail"
            icon = "✗"
        else:
            cls = "neutral"
            icon = "–"
        criteria_html += f"""
        <div class="score-criterion">
            <span>{c['label']}</span>
            <span class="{cls}">{icon} {c['note']}</span>
        </div>"""

    return f"""
    <div class="score-card">
        <div class="score-header">
            <div>
                <div class="score-name">{s['name']}</div>
                <div style="font-size:12px;color:var(--muted);margin-top:3px">{s['description']}</div>
            </div>
            <div class="score-badge {badge_class}">{score}<span style="font-size:14px;color:var(--muted)">/100</span></div>
        </div>
        <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:{score}%;background:{color}"></div>
        </div>
        {criteria_html}
    </div>
    """

SAFE_TICKERS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBAS3.SA", "WEGE3.SA",
    "RENT3.SA", "LREN3.SA", "MGLU3.SA", "BBDC4.SA", "ABEV3.SA",
    "EGIE3.SA", "TAEE11.SA", "TRPL4.SA", "CPLE6.SA", "SAPR11.SA",
    "BRKM5.SA", "UNIP6.SA", "SUZB3.SA", "KLBN11.SA", "CSNA3.SA",
    "GGBR4.SA", "USIM5.SA", "EMBR3.SA", "AZUL4.SA", "GOLL4.SA",
]
