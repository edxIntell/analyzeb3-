import streamlit as st

st.set_page_config(
    page_title="AnalyzeB3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
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
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background-color: var(--bg) !important; }

.hero {
    padding: 80px 40px 60px;
    text-align: center;
}
.hero-tag {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    border: 1px solid var(--accent);
    padding: 4px 14px;
    border-radius: 2px;
    margin-bottom: 28px;
}
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 64px;
    font-weight: 400;
    line-height: 1.1;
    margin: 0 0 20px;
    color: var(--text);
}
.hero h1 span { color: var(--accent); }
.hero p {
    font-size: 18px;
    color: var(--muted);
    max-width: 560px;
    margin: 0 auto 40px;
    line-height: 1.7;
    font-weight: 300;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin: 40px 0;
}
.feature-card {
    background: var(--surface);
    padding: 32px;
    transition: background 0.2s;
}
.feature-card:hover { background: var(--surface2); }
.feature-icon {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    letter-spacing: 2px;
    margin-bottom: 16px;
    display: block;
}
.feature-card h3 {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    font-weight: 400;
    margin: 0 0 10px;
    color: var(--text);
}
.feature-card p {
    font-size: 14px;
    color: var(--muted);
    line-height: 1.6;
    margin: 0;
}
.disclaimer {
    background: #1a1710;
    border: 1px solid #3d3520;
    border-left: 3px solid var(--accent3);
    border-radius: 8px;
    padding: 20px 24px;
    margin: 40px 0;
    font-size: 13px;
    color: #a89b6e;
    line-height: 1.6;
}
.disclaimer strong { color: var(--accent3); }

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-tag">Plataforma de Análise · B3</div>
    <h1>Investir com<br><span>clareza.</span></h1>
    <p>Análise técnica e fundamentalista integrada com as lentes de Lynch, Barsi e Dalio. Ferramenta — não recomendação.</p>
</div>

<div class="feature-grid">
    <div class="feature-card">
        <span class="feature-icon">01 · AT+AF</span>
        <h3>Ficha completa</h3>
        <p>Indicadores técnicos e fundamentalistas em uma tela só. RSI, MACD, P/L, ROE, EV/EBITDA e mais.</p>
    </div>
    <div class="feature-card">
        <span class="feature-icon">02 · FRAMEWORKS</span>
        <h3>Lentes de grandes</h3>
        <p>Score automático pelos critérios de Lynch, Barsi e Dalio. Dashboard comparativo lado a lado.</p>
    </div>
    <div class="feature-card">
        <span class="feature-icon">03 · COMPARATIVO</span>
        <h3>Multi-asset</h3>
        <p>Ações vs CDI, RF, ouro e commodities. Responda: vale o risco comparado com a renda fixa?</p>
    </div>
    <div class="feature-card">
        <span class="feature-icon">04 · SCREENER</span>
        <h3>Filtros combinados</h3>
        <p>Encontre ações que passam simultaneamente pelos filtros técnicos e fundamentalistas que você definir.</p>
    </div>
    <div class="feature-card">
        <span class="feature-icon">05 · MACRO</span>
        <h3>Cenário Dalio</h3>
        <p>Em qual quadrante macroeconômico o Brasil está agora. Quais ativos historicamente performam nesse regime.</p>
    </div>
    <div class="feature-card">
        <span class="feature-icon">06 · ALERTAS</span>
        <h3>Monitoramento</h3>
        <p>Receba notificações quando RSI cruzar limites, preço romper suporte ou indicador fundamentalista mudar.</p>
    </div>
</div>

<div class="disclaimer">
    <strong>Aviso importante:</strong> Esta plataforma é uma ferramenta de análise quantitativa automatizada. 
    Não constitui recomendação de compra ou venda de valores mobiliários. O usuário é responsável pelas 
    suas decisões de investimento. Nenhum dos indicadores ou scores apresentados configura consultoria financeira.
</div>
""", unsafe_allow_html=True)
