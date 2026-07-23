from pathlib import Path

ROOT = Path(__file__).parent.parent
DADOS_DIR = ROOT / "dados"
DADOS_BRUTOS_DIR = ROOT / "dados_brutos"
PERFIS_DIR = ROOT / "perfis"
HISTORICO_DIR = DADOS_DIR / "historico"
TORS_DIR = DADOS_BRUTOS_DIR / "tors"

EDITAIS_TODOS_FILE = DADOS_DIR / "editais_todos.json"
EDITAIS_PROCESSADOS_FILE = DADOS_DIR / "editais_processados.json"

OUTPUT_EXCEL = ROOT / "analise_editais_pnud.xlsx"
OUTPUT_PDF = ROOT / "relatorio_editais_pnud.pdf"

API_URL = "https://parceiros.undp.org.br/opportunities"
API_ENDPOINT = "icnim-api.undp.org.br/v1/publish/list/active"

CLASSIFICACAO_TIPOS = {
    "Consultoria Pessoa Física (PF)": [
        "pessoa física", "consultor pessoa física", "consultoria individual",
        "consultor individual", "consultor por produto"
    ],
    "Consultoria Pessoa Jurídica (PJ) / Empresa": [
        "pessoa jurídica", "empresa", "consultoria empresarial",
    ],
    "Consultoria Especializada (não especifica PF/PJ)": [
        "consultoria especializada", "consultor especializado",
    ],
    "Edital Genérico / IC": [
        "ic - undp", "individual contractor", "ic -",
    ],
}

AREAS_TEMATICAS = {
    "Tecnologia da Informação / Dados": [
        "dados", "python", "gis", "bi", "sei", "sic", "automação", "sistema",
        "software", "banco de dados", "prototipação", "tecnologia", "digital",
        "programação", "geoprocessamento", "geoespacial", "levantamento de requisitos",
        "proteção de dados", "privacidade", "lgpd", "repositório"
    ],
    "Economia / Finanças Públicas": [
        "tributação", "tributária", "carga tributária", "economia", "fiscal",
        "orçamento", "finanças", "bem-estar social"
    ],
    "Saúde": [
        "saúde", "hospitalar", "hospital", "médico", "clínico"
    ],
    "Estatística / Pesquisa / Metodologia": [
        "estatístico", "indicadores", "metodologia", "censo", "pesquisa",
        "dimensionamento", "estudo", "análise", "mapeamento", "sistematização"
    ],
    "Direito / Jurídico": [
        "jurídico", "legal", "penal", "vara", "cnj", "regulamentação",
        "normativo"
    ],
    "Meio Ambiente / Clima / Geografia": [
        "ambiental", "climático", "clima", "ecossistema", "costeiro",
        "geomorfológico", "geográfico", "territorial", "indígena",
        "comunidades tradicionais"
    ],
    "Gestão / Administração Pública": [
        "gestão", "administração", "processos", "governança", "força de trabalho",
        "diagnóstico institucional", "monitoramento", "avaliação"
    ],
}

DOMINIO_ORGAO = {
    "tcu.gov.br": "TCU",
    "ibge.gov.br": "IBGE",
    "gestao.gov.br": "MGI",
    "agu.gov.br": "AGU",
    "trabalho.gov.br": "MTE",
    "undp.org": "PNUD (Direto)",
}

PERFIS_DISPONIVEIS = ["engenheiro_dados", "economista", "ti_dados", "pesquisador", "juridico", "saude", "gestao", "ambiental"]
