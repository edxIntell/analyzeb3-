# AnalyzeB3 — Plataforma de Análise de Ações

Ferramenta de análise quantitativa de ações da B3. Análise técnica + fundamentalista + frameworks de grandes investidores.

> **Aviso:** Esta plataforma é uma ferramenta de análise. Não constitui recomendação de compra ou venda de valores mobiliários.

## Estrutura

```
app/
├── Home.py                   # Página inicial
├── utils.py                  # Dados, indicadores, scores
├── requirements.txt
└── pages/
    ├── 1_Ficha_Ativo.py      # AT + AF + Frameworks (Lynch, Barsi, Dalio)
    ├── 2_Comparativo.py      # Ações vs CDI, IBOV, Ouro, S&P500
    └── 3_Screener.py         # Filtros combinados AT+AF+Scores
```

## Setup local

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy no Streamlit Cloud

1. Suba este repositório no GitHub
2. Acesse https://share.streamlit.io
3. Conecte o repositório
4. Main file: `Home.py`
5. Deploy

## Funcionalidades

### Ficha de Ativo
- Candlestick com Bollinger Bands, MM20/50/200
- RSI (14) e MACD com histograma
- Volume colorido por direção
- Painel fundamentalista: P/L, ROE, EV/EBITDA, DY, Margem, Dívida
- Dashboard comparativo de frameworks:
  - **Lynch**: PEG, crescimento de lucro, P/L, endividamento
  - **Barsi**: Dividend Yield, Payout, ROE, setor defensivo
  - **Dalio**: Volatilidade, Sharpe, Max Drawdown, Beta

### Comparativo Multi-Asset
- Performance normalizada (base 100)
- Benchmarks: CDI, IPCA+6%, IBOV, Ouro, S&P500, Dólar
- Scatter risco × retorno
- Tabela com retorno/risco por ativo

### Screener
- Filtros técnicos: RSI, MM20, MM200
- Filtros fundamentalistas: P/L, DY, ROE
- Filtros de score: Lynch, Barsi, Dalio mínimos
- Analisa ~25 ações da B3

## Próximos passos
- [ ] Alertas via Telegram
- [ ] Autenticação e plano freemium
- [ ] Mais ações no screener
- [ ] Módulo macro (quadrante Dalio)
- [ ] FIIs e BDRs
