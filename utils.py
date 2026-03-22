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

def _brapi_token() -> str:
    try:
        return st.secrets["BRAPI_TOKEN"]
    except Exception:
        return ""

def _brapi_get(path: str, params: dict = {}) -> dict:
    """Faz requisição autenticada à brapi.dev."""
    token = _brapi_token()
    base  = "https://brapi.dev/api"
    p     = dict(params)
    if token:
        p["token"] = token
    r = requests.get(f"{base}{path}", params=p, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    symbol = ticker.upper().replace(".SA", "")
    range_map = {"6mo": "6mo", "1y": "1y", "2y": "2y", "3y": "3y"}
    try:
        data = _brapi_get(f"/quote/{symbol}", {
            "range": range_map.get(period, "1y"),
            "interval": "1d",
            "fundamental": "false",
            "history": "true",
        })
        results = data.get("results", [])
        if not results:
            return pd.DataFrame()
        hist = results[0].get("historicalDataPrice") or []
        rows = []
        for h in hist:
            c = h.get("close") or h.get("adjustedClose")
            if c is None:
                continue
            try:
                d = (pd.to_datetime(h["date"], unit="s")
                     if isinstance(h["date"], (int, float))
                     else pd.to_datetime(h["date"]))
                rows.append({
                    "Date":   d,
                    "Open":   h.get("open")   or c,
                    "High":   h.get("high")   or c,
                    "Low":    h.get("low")    or c,
                    "Close":  c,
                    "Volume": h.get("volume") or 0,
                })
            except Exception:
                continue
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).set_index("Date").sort_index()
        return df.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_fundamentals(ticker: str) -> dict:
    symbol = ticker.upper().replace(".SA", "")
    info   = {}
    try:
        data = _brapi_get(f"/quote/{symbol}", {"fundamental": "true"})
        results = data.get("results", [])
        if not results:
            return {}
        r = results[0]

        def g(key, default=None):
            return r.get(key, default)

        info["longName"]           = g("longName") or g("shortName", symbol)
        info["shortName"]          = g("shortName", symbol)
        info["sector"]             = g("sector", "")
        info["industry"]           = g("industry", "")
        info["longBusinessSummary"]= g("longBusinessSummary", "")
        info["currentPrice"]       = g("regularMarketPrice")
        info["regularMarketPrice"] = g("regularMarketPrice")
        info["marketCap"]          = g("marketCap")
        info["beta"]               = g("beta")
        # Valuation
        info["trailingPE"]         = g("trailingPE") or g("priceEarnings")
        info["forwardPE"]          = g("forwardPE")
        info["priceToBook"]        = g("priceToBook")
        info["enterpriseToEbitda"] = g("enterpriseToEbitda")
        info["enterpriseToRevenue"]= g("enterpriseToRevenue")
        info["priceToSalesTrailing12Months"] = g("priceToSalesTrailing12Months")
        # EPS / book (Graham)
        info["trailingEps"]        = g("epsTrailingTwelveMonths") or g("earningsPerShare")
        info["bookValue"]          = g("bookValue")
        # Dividendos
        info["dividendYield"]      = g("dividendYield") or g("trailingAnnualDividendYield")
        info["dividendRate"]       = g("dividendRate")  or g("trailingAnnualDividendRate")
        info["lastDividendValue"]  = g("lastDividendValue") or g("dividendRate")
        info["payoutRatio"]        = g("payoutRatio")
        # Rentabilidade
        info["returnOnEquity"]     = g("returnOnEquity")
        info["returnOnAssets"]     = g("returnOnAssets")
        info["profitMargins"]      = g("profitMargins")
        info["grossMargins"]       = g("grossMargins")
        info["operatingMargins"]   = g("operatingMargins")
        # Crescimento
        info["revenueGrowth"]      = g("revenueGrowth")
        info["earningsGrowth"]     = g("earningsGrowth")
        # Endividamento
        info["debtToEquity"]       = g("debtToEquity")
        info["currentRatio"]       = g("currentRatio")
        info["totalDebt"]          = g("totalDebt")
        info["totalCash"]          = g("totalCash")
        # FCF / EBITDA (DCF)
        info["freeCashflow"]       = g("freeCashflow")
        info["ebitda"]             = g("ebitda")
        info["sharesOutstanding"]  = g("sharesOutstanding")

        return {k: v for k, v in info.items() if v is not None}
    except Exception:
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_benchmark_returns(period: str = "1y") -> dict:
    """Retorna retornos de benchmarks via brapi (IBOV) e dados fixos para os demais."""
    results = {}
    # IBOV via brapi
    try:
        data = _brapi_get("/quote/%5EBVSP", {"range": period, "interval": "1d"})
        r = data.get("results", [{}])[0]
        hist = r.get("historicalDataPrice") or []
        closes = [h.get("close") for h in hist if h.get("close")]
        if len(closes) >= 2:
            results["IBOV"] = round((closes[-1] / closes[0] - 1) * 100, 1)
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


# ─── VALUATION MODELS ──────────────────────────────────────────────────────────

def valuation_graham(info: dict) -> dict:
    """Fórmula de Graham: V = sqrt(22.5 * LPA * VPA)"""
    try:
        eps = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
        bvps = info.get("bookValue")
        if eps and bvps and eps > 0 and bvps > 0:
            valor = (22.5 * eps * bvps) ** 0.5
            return {"modelo": "Graham", "valor": round(valor, 2),
                    "formula": "√(22.5 × LPA × VPA)",
                    "inputs": {"LPA": round(eps, 2), "VPA": round(bvps, 2)},
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "Graham", "valor": None, "valido": False,
            "motivo": "LPA ou VPA indisponível"}


def valuation_gordon(info: dict) -> dict:
    """Modelo de Gordon (DDM): P = DPS / (Ke - g)"""
    try:
        # DPS: prefere dividendRate (anual em R$), fallback yield*price
        dps = info.get("dividendRate")
        if not dps:
            dy = info.get("dividendYield")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if dy and price:
                dps = float(dy) * float(price)
        beta = float(info.get("beta") or 1.0)
        growth = float(info.get("earningsGrowth") or info.get("revenueGrowth") or 0.03)
        rf = 0.135
        premio = 0.05
        ke = rf + beta * premio
        g = min(growth, ke - 0.01)
        if dps and float(dps) > 0 and ke > g:
            valor = float(dps) / (ke - g)
            return {"modelo": "Gordon (DDM)", "valor": round(valor, 2),
                    "formula": "DPS / (Ke − g)",
                    "inputs": {"DPS": f"R$ {float(dps):.2f}", "Ke": f"{ke*100:.1f}%", "g": f"{g*100:.1f}%"},
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "Gordon (DDM)", "valor": None, "valido": False,
            "motivo": "Dividendo insuficiente ou empresa sem distribuição"}


def valuation_bazin(info: dict) -> dict:
    """Método Bazin: preço justo = DPA / 0.06 (yield mínimo 6%)"""
    try:
        dpa = info.get("dividendRate")
        if not dpa:
            dy = info.get("dividendYield")
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if dy and price:
                dpa = float(dy) * float(price)
        if dpa and float(dpa) > 0:
            valor = float(dpa) / 0.06
            return {"modelo": "Bazin", "valor": round(valor, 2),
                    "formula": "DPA / 6%",
                    "inputs": {"DPA anual": f"R$ {float(dpa):.2f}", "Yield mínimo": "6%"},
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "Bazin", "valor": None, "valido": False,
            "motivo": "Dividendo indisponível"}


def valuation_pl_setor(info: dict) -> dict:
    """Valuation por P/L setorial: usa P/L médio do setor como referência"""
    try:
        eps = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
        sector = info.get("sector", "")
        # P/L médio estimado por setor BR
        pl_setor = {
            "Financial Services": 9, "Financials": 9,
            "Basic Materials": 8, "Materials": 8,
            "Energy": 7, "Utilities": 12,
            "Consumer Staples": 16, "Consumer Defensive": 16,
            "Consumer Discretionary": 14, "Consumer Cyclical": 14,
            "Industrials": 13, "Healthcare": 18,
            "Technology": 20, "Communication Services": 12,
            "Real Estate": 15,
        }
        pl_ref = pl_setor.get(sector, 12)
        if eps and eps > 0:
            valor = eps * pl_ref
            return {"modelo": "P/L Setorial", "valor": round(valor, 2),
                    "formula": f"LPA × P/L médio do setor",
                    "inputs": {"LPA": round(eps, 2), "P/L setor": pl_ref, "Setor": sector or "Genérico"},
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "P/L Setorial", "valor": None, "valido": False,
            "motivo": "LPA indisponível"}


def valuation_ev_ebitda(info: dict) -> dict:
    """Valuation por EV/EBITDA: compara com múltiplo histórico de 7x"""
    try:
        ebitda = info.get("ebitda")
        shares = info.get("sharesOutstanding")
        debt = info.get("totalDebt") or 0
        cash = info.get("totalCash") or 0
        sector = info.get("sector", "")

        ev_ref = {"Utilities": 9, "Energy": 6, "Financial Services": 10,
                  "Technology": 15, "Consumer Staples": 12}.get(sector, 7)

        if ebitda and shares and ebitda > 0 and shares > 0:
            ev_justo = ebitda * ev_ref
            equity_justo = ev_justo - debt + cash
            valor = equity_justo / shares
            return {"modelo": "EV/EBITDA", "valor": round(valor, 2),
                    "formula": f"(EBITDA × {ev_ref}x − Dívida + Caixa) / Ações",
                    "inputs": {"EBITDA": f"R$ {ebitda/1e9:.1f}B", "EV/EBITDA ref": f"{ev_ref}x"},
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "EV/EBITDA", "valor": None, "valido": False,
            "motivo": "EBITDA ou dados de dívida indisponíveis"}


def valuation_dcf_simplificado(info: dict) -> dict:
    """DCF simplificado: usa FCF por ação com crescimento em 2 estágios"""
    try:
        fcf = info.get("freeCashflow")
        shares = info.get("sharesOutstanding")
        beta = info.get("beta") or 1.0
        growth_5a = min(float(info.get("earningsGrowth") or 0.05), 0.25)
        growth_terminal = 0.04  # crescimento perpétuo conservador

        if fcf and shares and fcf > 0 and shares > 0:
            fcf_share = fcf / shares
            rf = 0.135
            premio = 0.05
            wacc = rf + beta * premio

            # Estágio 1: 5 anos com crescimento estimado
            vp_fase1 = 0
            fcf_t = fcf_share
            for t in range(1, 6):
                fcf_t *= (1 + growth_5a)
                vp_fase1 += fcf_t / (1 + wacc) ** t

            # Estágio 2: valor terminal
            fcf_terminal = fcf_t * (1 + growth_terminal)
            vt = fcf_terminal / (wacc - growth_terminal)
            vp_terminal = vt / (1 + wacc) ** 5

            valor = vp_fase1 + vp_terminal
            return {"modelo": "DCF (2 estágios)", "valor": round(valor, 2),
                    "formula": "VP(FCF 5a) + VP(Valor Terminal)",
                    "inputs": {
                        "FCF/ação": f"R$ {fcf_share:.2f}",
                        "Crescimento 5a": f"{growth_5a*100:.1f}%",
                        "WACC": f"{wacc*100:.1f}%",
                        "g terminal": f"{growth_terminal*100:.1f}%"
                    },
                    "valido": True}
    except Exception:
        pass
    return {"modelo": "DCF (2 estágios)", "valor": None, "valido": False,
            "motivo": "Free Cash Flow indisponível"}


def compute_valuation(info: dict) -> dict:
    """Roda todos os modelos e retorna consenso."""
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    modelos = [
        valuation_graham(info),
        valuation_gordon(info),
        valuation_bazin(info),
        valuation_pl_setor(info),
        valuation_ev_ebitda(info),
        valuation_dcf_simplificado(info),
    ]
    validos = [m for m in modelos if m["valido"] and m["valor"] and m["valor"] > 0]
    consenso = round(sum(m["valor"] for m in validos) / len(validos), 2) if validos else None

    upside = None
    if consenso and price:
        upside = round((consenso / float(price) - 1) * 100, 1)

    return {
        "preco_atual": price,
        "consenso": consenso,
        "upside_pct": upside,
        "modelos": modelos,
        "validos": len(validos),
    }


# ─── SETOR PEERS ───────────────────────────────────────────────────────────────

SECTOR_PEERS = {
    # Petróleo & Gás
    "PETR4.SA": {"br": ["PETR3.SA","RECV3.SA","PRIO3.SA","RRRP3.SA"], "intl": ["XOM","CVX","PBR","SLB"]},
    "PETR3.SA": {"br": ["PETR4.SA","RECV3.SA","PRIO3.SA"], "intl": ["XOM","CVX","PBR"]},
    "PRIO3.SA": {"br": ["PETR4.SA","RECV3.SA","RRRP3.SA"], "intl": ["XOM","CVX","PBR"]},
    # Mineração & Siderurgia
    "VALE3.SA": {"br": ["CSNA3.SA","GGBR4.SA","USIM5.SA","GOAU4.SA"], "intl": ["RIO","BHP","SCCO","FCX"]},
    "CSNA3.SA": {"br": ["VALE3.SA","GGBR4.SA","USIM5.SA"], "intl": ["X","NUE","STLD"]},
    "GGBR4.SA": {"br": ["VALE3.SA","CSNA3.SA","USIM5.SA"], "intl": ["X","NUE","MT"]},
    # Petroquímica
    "BRKM5.SA": {"br": ["UNIP6.SA","SUZB3.SA","KLBN11.SA"], "intl": ["LYB","DOW","DD","BASFY"]},
    "UNIP6.SA": {"br": ["BRKM5.SA","SUZB3.SA"], "intl": ["LYB","DOW","DD"]},
    # Papel & Celulose
    "SUZB3.SA": {"br": ["KLBN11.SA","BRKM5.SA"], "intl": ["IP","WRK","PKG"]},
    "KLBN11.SA": {"br": ["SUZB3.SA","BRKM5.SA"], "intl": ["IP","WRK"]},
    # Bancos
    "ITUB4.SA": {"br": ["BBAS3.SA","BBDC4.SA","SANB11.SA","BMGB4.SA"], "intl": ["JPM","BAC","C","SAN"]},
    "BBAS3.SA": {"br": ["ITUB4.SA","BBDC4.SA","SANB11.SA"], "intl": ["JPM","BAC","ITUB"]},
    "BBDC4.SA": {"br": ["ITUB4.SA","BBAS3.SA","SANB11.SA"], "intl": ["JPM","BAC","SAN"]},
    # Energia Elétrica
    "EGIE3.SA": {"br": ["TAEE11.SA","TRPL4.SA","CPLE6.SA","ENGI11.SA","ENBR3.SA"], "intl": ["NEE","DUK","SO","ELP"]},
    "TAEE11.SA": {"br": ["EGIE3.SA","TRPL4.SA","CPLE6.SA","ENGI11.SA"], "intl": ["NEE","DUK","SO"]},
    "TRPL4.SA": {"br": ["EGIE3.SA","TAEE11.SA","CPLE6.SA"], "intl": ["NEE","DUK","ELP"]},
    # Saneamento
    "SAPR11.SA": {"br": ["SBSP3.SA","CSMG3.SA","TIMS3.SA"], "intl": ["AWK","WTR","WTRG"]},
    # Varejo
    "LREN3.SA": {"br": ["ARZZ3.SA","SOMA3.SA","GRND3.SA"], "intl": ["GPS","ANF","BURL"]},
    "MGLU3.SA": {"br": ["AMER3.SA","VIVA3.SA","LJQQ3.SA"], "intl": ["AMZN","WMT","TGT"]},
    # Aviação
    "AZUL4.SA": {"br": ["GOLL4.SA","EMBR3.SA"], "intl": ["DAL","UAL","LUV","AAL"]},
    "GOLL4.SA": {"br": ["AZUL4.SA","EMBR3.SA"], "intl": ["DAL","UAL","LUV","LATAM"]},
    # Tecnologia
    "INTB3.SA": {"br": ["TOTS3.SA","LWSA3.SA"], "intl": ["MSFT","AAPL","GOOGL","META"]},
    # Genérico por setor (fallback)
    "_energy":    {"br": ["PETR4.SA","PRIO3.SA","RECV3.SA"], "intl": ["XOM","CVX","BP"]},
    "_materials": {"br": ["VALE3.SA","GGBR4.SA","SUZB3.SA"], "intl": ["RIO","BHP","LYB"]},
    "_financials":{"br": ["ITUB4.SA","BBAS3.SA","BBDC4.SA"], "intl": ["JPM","BAC","SAN"]},
    "_utilities": {"br": ["EGIE3.SA","TAEE11.SA","TRPL4.SA"], "intl": ["NEE","DUK","ELP"]},
    "_consumer":  {"br": ["ABEV3.SA","LREN3.SA","MGLU3.SA"], "intl": ["KO","PEP","WMT"]},
    "_industrial":{"br": ["WEGE3.SA","EMBR3.SA","RENT3.SA"], "intl": ["GE","MMM","HON"]},
}

SECTOR_MAP = {
    "Energy": "_energy", "Basic Materials": "_materials", "Materials": "_materials",
    "Financial Services": "_financials", "Financials": "_financials",
    "Utilities": "_utilities", "Consumer Staples": "_consumer",
    "Consumer Defensive": "_consumer", "Consumer Discretionary": "_consumer",
    "Consumer Cyclical": "_consumer", "Industrials": "_industrial",
}

def get_peers(ticker: str, sector: str) -> dict:
    """Retorna lista de pares BR e internacionais para o ticker."""
    if ticker in SECTOR_PEERS:
        return SECTOR_PEERS[ticker]
    sector_key = SECTOR_MAP.get(sector, "")
    if sector_key and sector_key in SECTOR_PEERS:
        return SECTOR_PEERS[sector_key]
    return {"br": [], "intl": []}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_peer_data(tickers: list) -> list:
    """Busca dados básicos de múltiplos tickers para comparação setorial."""
    results = []
    for ticker in tickers:
        try:
            is_br = ticker.endswith(".SA")
            symbol = ticker
            info = {}

            # Yahoo quoteSummary para todos
            modules = "summaryDetail,defaultKeyStatistics,financialData,price"
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules={modules}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=15)

            if resp.status_code == 200:
                result = resp.json().get("quoteSummary", {}).get("result", [])
                if result:
                    r = result[0]
                    sd = r.get("summaryDetail", {})
                    ks = r.get("defaultKeyStatistics", {})
                    fd = r.get("financialData", {})
                    pr = r.get("price", {})

                    def raw(d, k):
                        v = d.get(k)
                        return v.get("raw") if isinstance(v, dict) else v

                    price = raw(pr, "regularMarketPrice") or raw(sd, "regularMarketPrice")
                    currency = pr.get("currency", "BRL" if is_br else "USD")
                    name = pr.get("shortName") or pr.get("longName") or ticker

                    info = {
                        "ticker":    ticker,
                        "nome":      name,
                        "moeda":     currency,
                        "preco":     price,
                        "pl":        raw(sd, "trailingPE") or raw(sd, "forwardPE"),
                        "pvp":       raw(ks, "priceToBook"),
                        "roe":       raw(fd, "returnOnEquity"),
                        "margem":    raw(fd, "profitMargins"),
                        "dy":        raw(sd, "dividendYield") or raw(sd, "trailingAnnualDividendYield"),
                        "ev_ebitda": raw(ks, "enterpriseToEbitda"),
                        "beta":      raw(ks, "beta") or raw(sd, "beta"),
                        "market_cap": raw(pr, "marketCap"),
                        "variacao_1d": raw(pr, "regularMarketChangePercent"),
                        "is_br":     is_br,
                    }
                    # Retorno 1 ano via histórico
                    try:
                        hist_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
                        hr = requests.get(hist_url, headers=headers, timeout=10).json()
                        closes = hr.get("chart",{}).get("result",[{}])[0].get("indicators",{}).get("quote",[{}])[0].get("close",[])
                        closes = [c for c in closes if c is not None]
                        if len(closes) >= 2:
                            info["ret_1a"] = round((closes[-1]/closes[0]-1)*100, 1)
                    except Exception:
                        pass

                    results.append(info)
        except Exception:
            continue
    return results
