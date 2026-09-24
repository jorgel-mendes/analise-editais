# 📋 Análise de Editais PNUD / UNESCO / OEI Brasil

### 👉 [Acessar o dashboard](https://jorgel-mendes.github.io/analise-editais/)
Atualizado automaticamente todo dia às 9h BRT.

Scraping, persistência e análise de editais (bidding notices) do PNUD, UNESCO e OEI no Brasil, com classificação automática por área, tipo e perfil profissional.

**Fontes**:
- PNUD — [parceiros.undp.org.br/opportunities](https://parceiros.undp.org.br/opportunities)
- UNESCO — [roster.brasilia.unesco.org](https://roster.brasilia.unesco.org/)
- OEI — [oei.int/licitaciones-y-convocatorias](https://oei.int/licitaciones-y-convocatorias/)

---

## Funcionalidades

- **Scraping diário multi-fonte** — PNUD via Playwright (API `icnim-api.undp.org.br`), UNESCO via API JSON pública, OEI via sitemap + páginas de detalhe
- **Persistência histórica** — snapshots diários com detecção de novos/encerrados, por fonte
- **Classificação automática** — tipo (PF/PJ), área temática, órgão parceiro, perfil profissional (IA via DeepSeek, com fallback determinístico)
- **4 perfis pré-configurados** — engenheiro_dados, economista, pesquisador_computacao, analista_powerbi
- **Match detalhado por edital** e **recomendações de estudo** (curto/médio/longo prazo) — calculados e gravados no JSON, mas hoje fora do dashboard público
- **Frontend SPA** — dashboard com filtros, cards de editais e detalhes (GitHub Pages)
- **Relatórios Excel + PDF** — gerados a cada execução completa, com aba/seção por fonte
- **Pipeline diário** — GitHub Actions (cron 9h BRT); a IA só roda em dias com edital novo

## Dashboard

- **Datas** — cada edital mostra quando foi publicado e o prazo final (dd/mm/aaaa)
- **Filtros** — área, fonte (PNUD/UNESCO/OEI), tipo, busca livre e "Ocultar prazo vencido" (marcado por padrão)
- **Selo 🟡 "Prazo vencido · ainda no portal"** — o prazo já passou, mas a fonte ainda publica o edital; o detalhe traz um aviso para conferir no portal
- **Abas** — ativos de hoje e histórico de 12 meses (🟢 aberto / 🔴 encerrado)
- **Links** — OEI abre a página do próprio edital; PNUD e UNESCO não têm página pública por edital, então o link vai para a listagem do portal, e a UNESCO ganha também um botão para o PDF do edital (só enquanto ele está ativo, porque a UNESCO remove o arquivo quando o edital fecha)

## Quando um edital é ativo ou encerrado

Um edital é **ativo** enquanto aparece na coleta do dia e **encerrado** quando some dela:

- **PNUD e UNESCO** — as APIs só devolvem o que está publicado; sai da API, sai da lista
- **OEI** — o campo "Estado" da página é lido; estados como adjudicado, desierto, cancelado ou cerrado encerram o edital. A busca olha páginas atualizadas nos últimos 60 dias
- **Regra dos 90 dias** — passados 90 dias do prazo final, o edital conta como encerrado mesmo que a fonte ainda o publique (`DIAS_APOS_PRAZO_ENCERRADO` em `core/scraper.py`)
- **Falha numa fonte** — os editais dela ficam como estavam no dia anterior, em vez de parecerem encerrados

A execução diária compara o dia com o snapshot anterior:

- **Com edital novo** — análise completa com IA, relatórios Excel/PDF e site regerados
- **Sem edital novo** — sem IA; o site é atualizado a partir da análise já publicada, removendo os encerrados e recalculando os números (`--force` força a análise completa)

## Estrutura

```
analise_editais/
├── main.py                  # CLI (click): daily, fetch, analyze, report, profiles, status, backfill-oei
├── core/
│   ├── config.py            # Constantes, classificações, caminhos, fontes disponíveis
│   ├── scraper.py           # Orquestrador multi-fonte — chama core/sources/* e persiste
│   ├── sources/
│   │   ├── __init__.py      # Links por fonte (portal, página do edital, PDF)
│   │   ├── pnud.py          # Playwright — intercepta API e captura editais
│   │   ├── unesco.py        # API JSON pública (apiroster.brasilia.unesco.org)
│   │   └── oei.py           # Sitemap XML + parsing de páginas de detalhe (HTML)
│   ├── persistence.py       # Snapshots históricos, deduplicação, detecção de novidades
│   ├── classifier.py        # Classifica tipo, área, órgão, valor de cada edital
│   ├── perfil.py            # Carrega perfis, pontua match edital↔perfil
│   ├── bridge.py            # Mescla qualificações extraídas dos ToRs (PDFs)
│   ├── analyzer.py          # Engine de análise com filtros de período, perfil e fonte
│   ├── recommender.py       # Recomendações de estudo por perfil (curto/médio/longo prazo)
│   ├── reporter.py          # Geração de relatórios Excel + PDF
│   ├── llm.py               # Classificação e recomendações via DeepSeek
│   ├── site_generator.py    # Gera JSON do frontend (com IA ou atualização sem IA)
│   ├── tor_pipeline.py      # Download (Playwright) + extração de ToRs — só PNUD
│   ├── tor_direct.py        # Download direto (HTTP) + extração de ToRs — UNESCO/OEI
│   └── tor_texts.py         # Texto dos ToRs, gravado comprimido e versionado
├── perfis/                  # Perfis profissionais em JSON (editáveis)
├── dados/                   # Persistência (editais_todos.json + snapshots)
├── dados_brutos/            # Dados crus do scraping + qualificações extraídas
│   ├── tors/                # PDFs/zips baixados (gitignored, efêmeros no CI)
│   └── tors_texto/          # Texto extraído dos ToRs em .txt.gz (versionado)
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
# Pipeline diário (scrape + análise + relatório + site; IA só com edital novo)
uv run analise-editais daily

# Forçar a análise completa mesmo sem edital novo
uv run analise-editais daily --force

# Apenas buscar e persistir editais
uv run analise-editais fetch

# Analisar últimos 3 meses (padrão)
uv run analise-editais analyze

# Analisar todos os editais
uv run analise-editais analyze --todos

# Filtrar por perfil
uv run analise-editais analyze --perfil engenheiro_dados

# Filtrar por fonte (pnud, unesco, oei)
uv run analise-editais analyze --fonte unesco

# Restringir o fetch/daily a uma ou mais fontes (padrão: todas)
uv run analise-editais fetch --fonte unesco --fonte oei

# Gerar relatórios
uv run analise-editais report

# Listar perfis
uv run analise-editais profiles

# Status dos dados (com contagem por fonte)
uv run analise-editais status

# Backfill pontual do histórico completo da OEI (via sitemap, ~1.100 páginas)
uv run analise-editais backfill-oei
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

O sistema classifica cada edital com o perfil mais compatível e gera recomendações de estudo. Esses resultados ficam em `docs/data/analise.json` e nos relatórios, mas não aparecem no dashboard público.

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
