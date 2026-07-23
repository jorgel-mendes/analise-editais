from collections import Counter

from core.perfil import carregar_perfil, carregar_perfis

CURSO_MAP = {
    # Ferramentas/tools
    "power bi": [
        {"curso": "Microsoft PL-300 — Power BI Data Analyst", "custo": "R$ 300 (prova)", "carga": "40h", "nivel": "Certificação", "link": "https://learn.microsoft.com/pt-br/certifications/power-bi-data-analyst-associate/"},
        {"curso": "Power BI Completo (Udemy)", "custo": "R$ 30", "carga": "20h", "nivel": "Curso", "link": "https://www.udemy.com/topic/power-bi/"},
    ],
    "power automate": [
        {"curso": "Microsoft PL-900 — Power Platform Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "link": "https://learn.microsoft.com/pt-br/certifications/power-platform-fundamentals/"},
    ],
    "power platform": [
        {"curso": "Microsoft PL-900 — Power Platform Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "link": "https://learn.microsoft.com/pt-br/certifications/power-platform-fundamentals/"},
    ],
    "sharepoint": [
        {"curso": "SharePoint Online (Microsoft Learn)", "custo": "Grátis", "carga": "10h", "nivel": "Curso", "link": "https://learn.microsoft.com/pt-br/training/sharepoint/"},
    ],
    "microsoft 365": [
        {"curso": "Microsoft 365 Fundamentals (MS-900)", "custo": "R$ 210 (prova)", "carga": "12h", "nivel": "Certificação", "link": "https://learn.microsoft.com/pt-br/certifications/microsoft-365-fundamentals/"},
    ],
    "python": [
        {"curso": "Python for Everybody (Coursera)", "custo": "Grátis (auxílio financeiro)", "carga": "80h", "nivel": "Curso", "link": "https://www.coursera.org/specializations/python"},
        {"curso": "Python para Ciência de Dados (DataCamp)", "custo": "US$ 25/mês", "carga": "60h", "nivel": "Curso", "link": "https://www.datacamp.com/tracks/data-scientist-with-python"},
    ],
    "sql": [
        {"curso": "SQL for Data Science (Coursera)", "custo": "Grátis (auxílio financeiro)", "carga": "20h", "nivel": "Curso", "link": "https://www.coursera.org/learn/sql-for-data-science"},
        {"curso": "SQL Completo (Udemy)", "custo": "R$ 30", "carga": "15h", "nivel": "Curso", "link": "https://www.udemy.com/topic/sql/"},
    ],
    "r": [
        {"curso": "R Programming (Coursera — Johns Hopkins)", "custo": "Grátis (auxílio financeiro)", "carga": "50h", "nivel": "Curso", "link": "https://www.coursera.org/learn/r-programming"},
    ],
    "qgis": [
        {"curso": "QGIS Básico (INPE)", "custo": "Grátis", "carga": "40h", "nivel": "Curso", "link": "http://www.dpi.inpe.br/cursos/"},
    ],
    "arcgis": [
        {"curso": "ArcGIS Pro Básico (ESRI Academy)", "custo": "Grátis (módulos básicos)", "carga": "24h", "nivel": "Curso", "link": "https://www.esri.com/training/"},
    ],
    "git": [
        {"curso": "Git e GitHub (Udemy)", "custo": "R$ 30", "carga": "8h", "nivel": "Curso", "link": "https://www.udemy.com/topic/git/"},
    ],
    "docker": [
        {"curso": "Docker para Desenvolvedores (Udemy)", "custo": "R$ 30", "carga": "12h", "nivel": "Curso", "link": "https://www.udemy.com/topic/docker/"},
    ],
    "azure": [
        {"curso": "Microsoft AZ-900 — Azure Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "link": "https://learn.microsoft.com/pt-br/certifications/azure-fundamentals/"},
    ],
    "aws": [
        {"curso": "AWS Cloud Practitioner", "custo": "US$ 100 (prova)", "carga": "20h", "nivel": "Certificação", "link": "https://aws.amazon.com/certification/certified-cloud-practitioner/"},
    ],
    "google cloud": [
        {"curso": "Google Cloud Digital Leader", "custo": "US$ 100 (prova)", "carga": "15h", "nivel": "Certificação", "link": "https://cloud.google.com/learn/certification"},
    ],
    "excel": [
        {"curso": "Excel Avançado (Udemy)", "custo": "R$ 30", "carga": "15h", "nivel": "Curso", "link": "https://www.udemy.com/topic/excel/"},
    ],
    "tableau": [
        {"curso": "Tableau Desktop Specialist", "custo": "US$ 100 (prova)", "carga": "20h", "nivel": "Certificação", "link": "https://www.tableau.com/learn/certification"},
    ],
    "stata": [
        {"curso": "Stata Fundamentals (StataCorp)", "custo": "Grátis (webinars)", "carga": "12h", "nivel": "Curso", "link": "https://www.stata.com/training/"},
    ],
    "spss": [
        {"curso": "SPSS para Pesquisa (Udemy)", "custo": "R$ 30", "carga": "12h", "nivel": "Curso", "link": "https://www.udemy.com/topic/spss/"},
    ],
    "sas": [
        {"curso": "SAS Programming (Coursera)", "custo": "Grátis (auxílio financeiro)", "carga": "40h", "nivel": "Curso", "link": "https://www.coursera.org/learn/sas-programming-basics"},
    ],
    "google earth engine": [
        {"curso": "Google Earth Engine (Google)", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "link": "https://developers.google.com/earth-engine/tutorials"},
    ],
    "matlab": [
        {"curso": "MATLAB Fundamentals (MathWorks)", "custo": "Grátis (Onramp)", "carga": "8h", "nivel": "Curso", "link": "https://matlabacademy.mathworks.com/"},
    ],
    "sei": [
        {"curso": "SEI! — Treinamento (ENAP)", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "sic": [
        {"curso": "SIC e Acesso à Informação (ENAP)", "custo": "Grátis", "carga": "16h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],

    # Idiomas
    "inglês": [
        {"curso": "Inglês para Fins Profissionais (Coursera)", "custo": "Grátis (auxílio financeiro)", "carga": "60h", "nivel": "Curso", "link": "https://www.coursera.org/specializations/english-for-business"},
    ],
    "espanhol": [
        {"curso": "Espanhol Básico (Duolingo / Busuu)", "custo": "Grátis", "carga": "50h", "nivel": "Curso", "link": "https://www.duolingo.com/course/es/pt"},
    ],

    # Graus acadêmicos
    "mestrado": [
        {"curso": "Mestrado Stricto Sensu (UFBA / universidade pública)", "custo": "Grátis (bolsa CAPES: R$ 2.100/mês)", "carga": "24 meses", "nivel": "Pós-graduação", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "doutorado": [
        {"curso": "Doutorado Stricto Sensu (UFBA / universidade pública)", "custo": "Grátis (bolsa CAPES: R$ 3.100/mês)", "carga": "48 meses", "nivel": "Pós-graduação", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "pós-graduação": [
        {"curso": "Especialização / MBA (UFBA, USP/ESALQ, FGV)", "custo": "R$ 0–700/mês", "carga": "12–18 meses", "nivel": "Pós-graduação", "link": "https://www.ufba.br/pos-graduacao"},
    ],

    # Certificações gerais
    "scrum": [
        {"curso": "PSM I — Professional Scrum Master", "custo": "US$ 150 (prova)", "carga": "20h", "nivel": "Certificação", "link": "https://www.scrum.org/assessments/professional-scrum-master-i-certification"},
    ],
    "pmp": [
        {"curso": "PMP — Project Management Professional", "custo": "US$ 555 (prova)", "carga": "80h", "nivel": "Certificação", "link": "https://www.pmi.org/certifications/project-management-pmp"},
    ],
    "lgpd": [
        {"curso": "LGPD e Proteção de Dados (ENAP)", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],

    # Áreas/geral
    "gestão pública": [
        {"curso": "Gestão Pública (ENAP)", "custo": "Grátis", "carga": "40h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "gestão de projetos": [
        {"curso": "Gestão de Projetos (ENAP / FGV Online)", "custo": "Grátis", "carga": "30h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "políticas públicas": [
        {"curso": "Avaliação de Políticas Públicas (ENAP/TCU)", "custo": "Grátis", "carga": "30h", "nivel": "Curso", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "metodologia científica": [
        {"curso": "Metodologia Científica (Coursera / USP)", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "link": "https://www.coursera.org/learn/metodologia-cientifica"},
    ],
    "análise de dados": [
        {"curso": "Google Data Analytics Certificate (Coursera)", "custo": "Grátis (auxílio financeiro)", "carga": "180h", "nivel": "Certificado profissional", "link": "https://www.coursera.org/professional-certificates/google-data-analytics"},
    ],
}


def mapear_curso(ferramenta: str) -> list[dict]:
    """Retorna cursos sugeridos para uma ferramenta/competência."""
    key = ferramenta.lower().strip()
    if key in CURSO_MAP:
        return CURSO_MAP[key]
    for k, v in CURSO_MAP.items():
        if k in key or key in k:
            return v
    return [{"curso": f"Aprenda {ferramenta} (busque na Udemy/Coursera)", "custo": "Variável", "carga": "Variável", "nivel": "Curso", "link": "https://www.udemy.com/"}]


def gerar_recomendacoes(editais: list, perfil_nome: str) -> dict:
    """Gera recomendações de estudo personalizadas para um perfil."""
    perfil = carregar_perfil(perfil_nome)
    if not perfil:
        return {"perfil": perfil_nome, "erro": "Perfil não encontrado"}

    perfil_ferr = set(f.lower() for f in perfil.get("ferramentas", []))
    perfil_grad = set(g.lower() for g in perfil.get("graduacoes", []))
    perfil_lang = set(l.lower() for l in perfil.get("idiomas", []))

    ferramentas_demand = Counter()
    graduacoes_demand = Counter()
    idiomas_demand = Counter()
    valor_por_ferramenta = Counter()
    valor_por_graduacao = Counter()
    editais_com_match = 0
    valor_total_oportunidades = 0

    for e in editais:
        match_data = e.get("matches", {}).get(perfil_nome, {})
        score = match_data.get("score", 0)
        if score < 0.15:
            continue
        editais_com_match += 1
        req = e.get("requisitos", {})

        for f in req.get("ferramentas", []):
            f_lower = f.lower()
            if f_lower not in perfil_ferr:
                ferramentas_demand[f_lower] += 1
                valor = e.get("valor_estimado_num") or 0
                if valor:
                    valor_por_ferramenta[f_lower] += valor

        for g in req.get("graduacao", []):
            g_lower = g.lower()
            if not any(pg in g_lower or g_lower in pg for pg in perfil_grad):
                graduacoes_demand[g_lower] += 1
                valor = e.get("valor_estimado_num") or 0
                if valor:
                    valor_por_graduacao[g_lower] += valor

        for lang in req.get("idiomas", []):
            l_lower = lang.lower()
            if l_lower not in perfil_lang:
                idiomas_demand[l_lower] += 1

        valor = e.get("valor_estimado_num") or 0
        if valor:
            valor_total_oportunidades += valor

    gaps = []

    # Gaps de ferramentas
    for ferramenta, count in ferramentas_demand.most_common(10):
        cursos = mapear_curso(ferramenta)
        valor_total = valor_por_ferramenta.get(ferramenta, 0)
        gaps.append({
            "tipo": "ferramenta",
            "nome": ferramenta,
            "editais": count,
            "impacto_financeiro": round(valor_total, 2) if valor_total else None,
            "cursos": cursos[:2],
            "prioridade": "alta" if count >= 3 else ("média" if count >= 1 else "baixa"),
        })

    # Gaps de graduação
    for grad, count in graduacoes_demand.most_common(6):
        valor_total = valor_por_graduacao.get(grad, 0)
        gaps.append({
            "tipo": "graduacao",
            "nome": grad,
            "editais": count,
            "impacto_financeiro": round(valor_total, 2) if valor_total else None,
            "cursos": mapear_curso(grad)[:2] if mapear_curso(grad) else [],
            "prioridade": "alta" if count >= 2 else "média",
        })

    # Gaps de idiomas
    for lang, count in idiomas_demand.most_common(4):
        gaps.append({
            "tipo": "idioma",
            "nome": lang,
            "editais": count,
            "impacto_financeiro": None,
            "cursos": mapear_curso(lang)[:2],
            "prioridade": "média" if count >= 1 else "baixa",
        })

    # Sugerir mestrado/doutorado se muitos editais exigem
    editais_com_mestrado = sum(1 for e in editais if e.get("requisitos", {}).get("mestrado"))
    editais_com_doutorado = sum(1 for e in editais if e.get("requisitos", {}).get("doutorado"))
    editais_com_pos = sum(1 for e in editais if e.get("requisitos", {}).get("pos_graduacao"))

    if editais_com_mestrado >= 2:
        gaps.append({
            "tipo": "formacao",
            "nome": "Mestrado Stricto Sensu",
            "editais": editais_com_mestrado,
            "impacto_financeiro": None,
            "cursos": mapear_curso("mestrado"),
            "prioridade": "alta" if editais_com_mestrado >= 4 else "média",
            "nota": f"{editais_com_mestrado} editais exigem ou pontuam mestrado",
        })

    if editais_com_doutorado >= 2:
        gaps.append({
            "tipo": "formacao",
            "nome": "Doutorado",
            "editais": editais_com_doutorado,
            "impacto_financeiro": None,
            "cursos": mapear_curso("doutorado"),
            "prioridade": "média",
            "nota": f"{editais_com_doutorado} editais pontuam doutorado",
        })

    if editais_com_pos >= 2:
        gaps.append({
            "tipo": "formacao",
            "nome": "Pós-graduação / Especialização",
            "editais": editais_com_pos,
            "impacto_financeiro": None,
            "cursos": mapear_curso("pós-graduação"),
            "prioridade": "média",
            "nota": f"{editais_com_pos} editais pontuam pós-graduação",
        })

    gaps.sort(key=lambda g: g["editais"], reverse=True)

    custo_total_estimado = 0
    cursos_prioritarios = []
    for g in gaps[:5]:
        if g["cursos"]:
            c = g["cursos"][0]
            cursos_prioritarios.append({
                "gap": g["nome"],
                "curso": c["curso"],
                "custo": c["custo"],
                "carga": c["carga"],
                "link": c["link"],
            })
            try:
                custo_str = c["custo"].replace("R$ ", "").replace(".", "").split(" ")[0]
                custo_total_estimado += float(custo_str) if custo_str.replace(",", ".").replace(".", "", 1).isdigit() else 0
            except ValueError:
                pass

    return {
        "perfil": perfil_nome,
        "descricao": perfil.get("descricao", ""),
        "total_editais_compativeis": editais_com_match,
        "valor_total_oportunidades": round(valor_total_oportunidades, 2),
        "gaps": gaps,
        "cursos_prioritarios": cursos_prioritarios,
        "custo_total_estimado_mensal": round(custo_total_estimado, 2) if custo_total_estimado else None,
    }


def gerar_recomendacoes_todos_perfis(editais: list) -> dict:
    """Gera recomendações para todos os perfis disponíveis."""
    perfis = carregar_perfis()
    recomendacoes = {}
    for nome in perfis:
        recomendacoes[nome] = gerar_recomendacoes(editais, nome)
    return recomendacoes
