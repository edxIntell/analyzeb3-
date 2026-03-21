import streamlit as st
import numpy as np
import json
import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def _get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None

def _safe_float(v, decimals=2):
    try:
        return round(float(v), decimals) if v is not None else None
    except:
        return None

def build_analysis_context(ticker: str, name: str, info: dict, df, scores: list) -> dict:
    close = df["Close"].dropna()

    def ret(col):
        s = df[col].dropna() if col in df.columns else None
        return _safe_float(s.iloc[-1], 1) if s is not None and len(s) > 0 else None

    bb_pos = None
    if "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        upper = df["BB_Upper"].dropna()
        lower = df["BB_Lower"].dropna()
        if len(upper) > 0 and len(lower) > 0:
            price = float(close.iloc[-1])
            u, l = float(upper.iloc[-1]), float(lower.iloc[-1])
            if u != l:
                bb_pos = round((price - l) / (u - l) * 100, 1)

    ma_trend = {}
    price = float(close.iloc[-1])
    for ma, col in [("MM20", "MA20"), ("MM50", "MA50"), ("MM200", "MA200")]:
        if col in df.columns:
            s = df[col].dropna()
            if len(s) > 0:
                val = float(s.iloc[-1])
                ma_trend[ma] = {"valor": round(val, 2), "acima": price > val}

    macd_signal = None
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        m = df["MACD"].dropna()
        ms = df["MACD_Signal"].dropna()
        if len(m) > 1 and len(ms) > 1:
            macd_signal = "cruzamento_alta" if (float(m.iloc[-1]) > float(ms.iloc[-1]) and
                                                 float(m.iloc[-2]) <= float(ms.iloc[-2])) \
                     else "cruzamento_baixa" if (float(m.iloc[-1]) < float(ms.iloc[-1]) and
                                                  float(m.iloc[-2]) >= float(ms.iloc[-2])) \
                     else "acima_sinal" if float(m.iloc[-1]) > float(ms.iloc[-1]) \
                     else "abaixo_sinal"

    rolling_max = close.rolling(252, min_periods=1).max()
    drawdown = (close - rolling_max) / rolling_max * 100
    max_dd = round(float(drawdown.min()), 1)

    ctx = {
        "ticker": ticker,
        "nome": name,
        "setor": info.get("sector", "N/D"),
        "industria": info.get("industry", "N/D"),
        "preco_atual": round(price, 2),
        "variacao_hoje_pct": ret("Return_1d"),
        "tecnico": {
            "rsi_14": _safe_float(df["RSI"].dropna().iloc[-1], 1) if "RSI" in df.columns and len(df["RSI"].dropna()) > 0 else None,
            "macd_situacao": macd_signal,
            "bollinger_posicao_pct": bb_pos,
            "medias_moveis": ma_trend,
            "retorno_1m": ret("Return_1m"),
            "retorno_3m": ret("Return_3m"),
            "retorno_6m": ret("Return_6m"),
            "retorno_1a": ret("Return_1y"),
            "volatilidade_anualizada_pct": _safe_float(df["Volatility_30d"].dropna().iloc[-1], 1) if "Volatility_30d" in df.columns and len(df["Volatility_30d"].dropna()) > 0 else None,
            "max_drawdown_1a_pct": max_dd,
        },
        "fundamentalista": {
            "pl_trailing": _safe_float(info.get("trailingPE"), 1),
            "pl_forward": _safe_float(info.get("forwardPE"), 1),
            "pvp": _safe_float(info.get("priceToBook"), 2),
            "ev_ebitda": _safe_float(info.get("enterpriseToEbitda"), 1),
            "roe_pct": _safe_float((info.get("returnOnEquity") or 0) * 100, 1),
            "roa_pct": _safe_float((info.get("returnOnAssets") or 0) * 100, 1),
            "margem_liquida_pct": _safe_float((info.get("profitMargins") or 0) * 100, 1),
            "margem_bruta_pct": _safe_float((info.get("grossMargins") or 0) * 100, 1),
            "dividend_yield_pct": _safe_float((info.get("dividendYield") or 0) * 100, 2),
            "payout_pct": _safe_float((info.get("payoutRatio") or 0) * 100, 1),
            "divida_pl": _safe_float((info.get("debtToEquity") or 0) / 100, 2),
            "crescimento_receita_pct": _safe_float((info.get("revenueGrowth") or 0) * 100, 1),
            "crescimento_lucro_pct": _safe_float((info.get("earningsGrowth") or 0) * 100, 1),
            "beta": _safe_float(info.get("beta"), 2),
        },
        "frameworks": {
            s["name"]: {
                "score": int(s["score"]),
                "criterios": [
                    {
                        "label": c["label"],
                        "pass": bool(c["pass"]) if c["pass"] is not None else None,
                        "note": c["note"]
                    }
                    for c in s["criteria"]
                ]
            }
            for s in scores
        },
        "cdi_referencia_pct": 10.5,
    }
    return ctx


def generate_analysis(ctx: dict) -> str:
    api_key = _get_api_key()

    system_prompt = """Você é um analista quantitativo de renda variável especializado no mercado brasileiro.
Você recebe dados estruturados de uma ação e produz uma análise técnica e fundamentalista integrada.

REGRAS ABSOLUTAS:
- NUNCA recomende comprar, vender ou manter a ação. Nunca use os verbos "comprar", "vender", "acumular", "realizar".
- Use frases como "os indicadores sugerem", "o dado aponta para", "tecnicamente observa-se", "do ponto de vista fundamentalista".
- Seja objetivo, preciso e use os dados fornecidos. Não invente dados.
- Escreva em português brasileiro, tom profissional mas acessível.
- Use markdown para formatar (##, **negrito**, listas com -).
- Estruture em 4 seções: Visão Geral, Análise Técnica, Análise Fundamentalista, Leitura pelos Frameworks.
- Termine com um parágrafo de síntese integrando as três perspectivas.
- Extensão: 400 a 600 palavras."""

    user_prompt = f"""Analise a seguinte ação com os dados abaixo:

```json
{json.dumps(ctx, ensure_ascii=False, indent=2)}
```

Produza uma análise estruturada conforme as instruções do sistema."""

    headers = {"Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    if api_key:
        headers["x-api-key"] = api_key

    response = requests.post(
        ANTHROPIC_API_URL,
        headers=headers,
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        },
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"Erro na API: {response.status_code} — {response.text[:200]}")

    data = response.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return text


def render_analysis_section(ticker: str, name: str, info: dict, df, scores: list):
    api_key = _get_api_key()

    st.markdown("""
    <div style="margin-top:40px;margin-bottom:8px">
        <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:3px;color:#c8f564;text-transform:uppercase;margin-bottom:6px">
            ANÁLISE QUANTITATIVA · IA
        </div>
        <div style="font-family:'DM Serif Display',serif;font-size:24px;color:var(--text);margin-bottom:4px">
            Leitura integrada AT + AF + Frameworks
        </div>
        <div style="font-size:13px;color:#6b7080;margin-bottom:20px">
            Gerada automaticamente com base nos indicadores calculados. Não constitui recomendação de investimento.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not api_key:
        st.warning(
            "Chave da API Anthropic não configurada. "
            "Adicione `ANTHROPIC_API_KEY` em `.streamlit/secrets.toml` para habilitar a análise por IA.",
            icon="🔑"
        )
        return

    if st.button("⚡ Gerar Análise", key="btn_analise"):
        ctx = build_analysis_context(ticker, name, info, df, scores)

        with st.spinner("Analisando indicadores e gerando síntese..."):
            try:
                analysis_text = generate_analysis(ctx)
                st.session_state["last_analysis"] = analysis_text
                st.session_state["last_analysis_ticker"] = ticker
            except Exception as e:
                st.error(f"Erro ao gerar análise: {e}")
                return

    if st.session_state.get("last_analysis") and st.session_state.get("last_analysis_ticker") == ticker:
        analysis = st.session_state["last_analysis"]
        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid #c8f564;border-radius:10px;padding:28px 32px;margin-top:16px;line-height:1.75;font-size:14px;color:var(--text)">
        {_md_to_html(analysis)}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:11px;color:#3d4050;margin-top:10px;font-family:'DM Mono',monospace">
            Análise gerada por IA com dados públicos. Não constitui recomendação de investimento.
            O usuário é responsável por suas decisões.
        </div>
        """, unsafe_allow_html=True)


def _md_to_html(text: str) -> str:
    import re
    text = re.sub(r'^## (.+)$', r'<h3 style="font-family:\'DM Serif Display\',serif;font-weight:400;color:var(--text);margin:20px 0 8px">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h4 style="font-family:\'DM Mono\',monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#c8f564;margin:16px 0 6px">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:var(--text)">\1</strong>', text)
    text = re.sub(r'^- (.+)$', r'<li style="margin:4px 0;color:#a0a6b8">\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li.*</li>\n?)+', r'<ul style="padding-left:20px;margin:8px 0">\g<0></ul>', text)
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('<'):
            result.append(line)
        else:
            result.append(f'<p style="margin:8px 0;color:#a0a6b8">{line}</p>')
    return '\n'.join(result)
