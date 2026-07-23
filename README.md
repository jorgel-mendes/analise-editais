# 📋 Análise de Editais PNUD Brasil

Scraping, persistência e análise de editais (bidding notices) do PNUD Brasil com classificação automática por perfil profissional e recomendações de estudo personalizadas.

**Fonte**: [parceiros.undp.org.br/opportunities](https://parceiros.undp.org.br/opportunities)

---

## Funcionalidades

- **Scraping diário** — captura editais ativos via Playwright (API `icnim-api.undp.org.br`)
- **Persistência histórica** — snapshots diários com detecção de novos/encerrados
- **Classificação automática** — tipo (PF/PJ), área temática, órgão parceiro, perfil profissional
- **8 perfis pré-configurados** — engenheiro_dados, economista, ti_dados, pesquisador, jurídico, saúde, gestão, ambiental
- **Match detalhado por edital** — graduação, ferramentas, idiomas, valor vs. perfil
- **Recomendações de estudo** — segmentadas em curto/médio/longo prazo, baseadas no histórico de 12 meses
- **Frontend SPA** — dashboard com filtros, cards de editais e detalhes (GitHub Pages)
- **Relatórios Excel + PDF** — gerados a cada execução
- **Pipeline diário** — GitHub Actions (cron 9h BRT), custo R$ 0

## Estrutura

```
analise_editais/
├── main.py                  # CLI (click): daily, fetch, analyze, report, profiles, status
├── core/
│   ├── config.py            # Constantes, classificações, caminhos
│   ├── scraper.py           # Playwright — intercepta API e captura editais
│   ├── persistence.py       # Snapshots históricos, deduplicação, detecção de novidades
│   ├── classifier.py        # Classifica tipo, área, órgão de cada edital
│   ├── perfil.py            # Carrega perfis, pontua match edital↔perfil
│   ├── bridge.py            # Mescla qualificações extraídas dos ToRs (PDFs)
│   ├── analyzer.py          # Engine de análise com filtros de período e perfil
│   ├── recommender.py       # Recomendações de estudo por perfil (curto/médio/longo prazo)
│   ├── reporter.py          # Geração de relatórios Excel + PDF
│   └── site_generator.py    # Gera JSON consumido pelo frontend
├── perfis/                  # Perfis profissionais em JSON (editáveis)
├── dados/                   # Persistência (editais_todos.json + snapshots)
├── dados_brutos/            # Dados crus do scraping + qualificações extraídas
├── docs/                    # Frontend SPA (GitHub Pages)
│   ├── index.html
│   └── data/
└── .github/workflows/       # CI/CD — daily cron
```

## Uso

### Instalação

```bash
git clone https://github.com/jorgel-mendes/analise-editais.git
cd analise-editais
uv sync
playwright install --with-deps chromium
```

### Comandos

```bash
# Pipeline completo (scrape + análise + relatório + site)
uv run analise-editais daily

# Apenas buscar e persistir editais
uv run analise-editais fetch

# Analisar últimos 3 meses (padrão)
uv run analise-editais analyze

# Analisar todos os editais
uv run analise-editais analyze --todos

# Filtrar por perfil
uv run analise-editais analyze --perfil engenheiro_dados

# Gerar relatórios
uv run analise-editais report

# Listar perfis
uv run analise-editais profiles

# Status dos dados
uv run analise-editais status
```

### Perfis personalizados

Crie arquivos JSON em `perfis/`:

```json
{
  "nome": "meu_perfil",
  "descricao": "Cientista de dados com foco em saúde pública",
  "graduacoes": ["ciência de dados", "estatística", "saúde pública"],
  "ferramentas": ["python", "r", "sql", "power bi"],
  "areas_interesse": ["Saúde", "Estatística / Pesquisa / Metodologia"],
  "idiomas": ["inglês"],
  "valor_minimo": 60000
}
```

O sistema automaticamente classifica cada edital com o perfil mais compatível e gera recomendações de estudo.

## Recomendações de estudo

Baseadas nos editais dos **últimos 12 meses**, segmentadas por horizonte:

| Prazo | Duração | Exemplos |
|-------|---------|----------|
| ⚡ Curto | 3-6 meses | PL-300 Power BI, QGIS (INPE), LGPD (ENAP), R/Python |
| 📈 Médio | 6-18 meses | MBA FGV, Especialização UFBA, Google Data Analytics |
| 🎓 Longo | 1-3 anos | Mestrado UFBA, Doutorado, certificações avançadas (AWS, Azure) |

Cada recomendação inclui: nome do curso, custo, carga horária, nível e link direto.

## Stack

- **Python 3.12** + Playwright (scraping)
- **click** (CLI) · **pandas + openpyxl** (Excel) · **fpdf2** (PDF) · **pdfplumber** (extração de ToRs)
- **GitHub Actions** (cron) · **GitHub Pages** (frontend)
- Vanilla JS/CSS (SPA sem dependências externas)

## Licença

MIT
