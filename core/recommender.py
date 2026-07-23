from collections import Counter

from core.perfil import carregar_perfil, carregar_perfis

# prazo: curto = até 6 meses, medio = 6-18 meses, longo = 1-3 anos
CURSO_MAP = {
    "power bi": [
        {"curso": "Power BI Completo — Udemy", "custo": "R$ 30", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/power-bi/"},
        {"curso": "Microsoft PL-300 — Power BI Data Analyst", "custo": "R$ 300 (prova)", "carga": "40h", "nivel": "Certificação", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/certifications/power-bi-data-analyst-associate/"},
    ],
    "power automate": [
        {"curso": "Microsoft PL-900 — Power Platform Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/certifications/power-platform-fundamentals/"},
    ],
    "power platform": [
        {"curso": "Microsoft PL-900 — Power Platform Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/certifications/power-platform-fundamentals/"},
    ],
    "sharepoint": [
        {"curso": "SharePoint Online — Microsoft Learn", "custo": "Grátis", "carga": "10h", "nivel": "Curso", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/training/sharepoint/"},
    ],
    "microsoft 365": [
        {"curso": "Microsoft 365 Fundamentals (MS-900)", "custo": "R$ 210 (prova)", "carga": "12h", "nivel": "Certificação", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/certifications/microsoft-365-fundamentals/"},
    ],
    "python": [
        {"curso": "Python para Ciência de Dados — DataCamp", "custo": "US$ 25/mês", "carga": "60h", "nivel": "Curso", "prazo": "curto", "link": "https://www.datacamp.com/tracks/data-scientist-with-python"},
        {"curso": "Google Data Analytics Certificate — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "180h", "nivel": "Certificado profissional", "prazo": "medio", "link": "https://www.coursera.org/professional-certificates/google-data-analytics"},
        {"curso": "Especialização em Ciência de Dados — USP/ESALQ (EAD)", "custo": "~R$ 500/mês", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.esalq.usp.br/"},
        {"curso": "Mestrado em Ciência de Dados / Computação — UFBA", "custo": "Grátis", "carga": "24 meses", "nivel": "Mestrado", "prazo": "longo", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "sql": [
        {"curso": "SQL Completo — Udemy", "custo": "R$ 30", "carga": "15h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/sql/"},
        {"curso": "SQL for Data Science — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/learn/sql-for-data-science"},
    ],
    "r": [
        {"curso": "R Programming — Coursera (Johns Hopkins)", "custo": "Grátis (auxílio financeiro)", "carga": "50h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/learn/r-programming"},
    ],
    "qgis": [
        {"curso": "QGIS Básico — INPE", "custo": "Grátis", "carga": "40h", "nivel": "Curso", "prazo": "curto", "link": "http://www.dpi.inpe.br/cursos/"},
        {"curso": "Geoprocessamento com Python + QGIS — INPE", "custo": "Grátis", "carga": "60h", "nivel": "Curso", "prazo": "medio", "link": "http://www.dpi.inpe.br/cursos/"},
    ],
    "arcgis": [
        {"curso": "ArcGIS Pro Básico — ESRI Academy", "custo": "Grátis (módulos básicos)", "carga": "24h", "nivel": "Curso", "prazo": "curto", "link": "https://www.esri.com/training/"},
    ],
    "git": [
        {"curso": "Git e GitHub — Udemy", "custo": "R$ 30", "carga": "8h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/git/"},
    ],
    "docker": [
        {"curso": "Docker para Desenvolvedores — Udemy", "custo": "R$ 30", "carga": "12h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/docker/"},
    ],
    "azure": [
        {"curso": "Microsoft AZ-900 — Azure Fundamentals", "custo": "R$ 210 (prova)", "carga": "15h", "nivel": "Certificação", "prazo": "curto", "link": "https://learn.microsoft.com/pt-br/certifications/azure-fundamentals/"},
        {"curso": "Microsoft DP-203 — Azure Data Engineer", "custo": "R$ 500 (prova)", "carga": "80h", "nivel": "Certificação", "prazo": "medio", "link": "https://learn.microsoft.com/pt-br/certifications/azure-data-engineer/"},
    ],
    "aws": [
        {"curso": "AWS Cloud Practitioner", "custo": "US$ 100 (prova)", "carga": "20h", "nivel": "Certificação", "prazo": "curto", "link": "https://aws.amazon.com/certification/certified-cloud-practitioner/"},
        {"curso": "AWS Solutions Architect Associate", "custo": "US$ 150 (prova)", "carga": "80h", "nivel": "Certificação", "prazo": "medio", "link": "https://aws.amazon.com/certification/certified-solutions-architect-associate/"},
    ],
    "google cloud": [
        {"curso": "Google Cloud Digital Leader", "custo": "US$ 100 (prova)", "carga": "15h", "nivel": "Certificação", "prazo": "curto", "link": "https://cloud.google.com/learn/certification"},
    ],
    "excel": [
        {"curso": "Excel Avançado — Udemy", "custo": "R$ 30", "carga": "15h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/excel/"},
    ],
    "tableau": [
        {"curso": "Tableau Desktop Specialist", "custo": "US$ 100 (prova)", "carga": "20h", "nivel": "Certificação", "prazo": "curto", "link": "https://www.tableau.com/learn/certification"},
    ],
    "stata": [
        {"curso": "Stata Fundamentals — StataCorp", "custo": "Grátis (webinars)", "carga": "12h", "nivel": "Curso", "prazo": "curto", "link": "https://www.stata.com/training/"},
    ],
    "spss": [
        {"curso": "SPSS para Pesquisa — Udemy", "custo": "R$ 30", "carga": "12h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/topic/spss/"},
    ],
    "sas": [
        {"curso": "SAS Programming — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "40h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/learn/sas-programming-basics"},
    ],
    "google earth engine": [
        {"curso": "Google Earth Engine — Google", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://developers.google.com/earth-engine/tutorials"},
    ],
    "matlab": [
        {"curso": "MATLAB Fundamentals — MathWorks", "custo": "Grátis (Onramp)", "carga": "8h", "nivel": "Curso", "prazo": "curto", "link": "https://matlabacademy.mathworks.com/"},
    ],
    "sei": [
        {"curso": "SEI! Treinamento — ENAP", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "sic": [
        {"curso": "SIC e Acesso à Informação — ENAP", "custo": "Grátis", "carga": "16h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "powerpoint": [
        {"curso": "PowerPoint para Apresentações Profissionais — Udemy", "custo": "R$ 30", "carga": "8h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/"},
    ],
    "word": [
        {"curso": "Word Avançado para Relatórios — Udemy", "custo": "R$ 30", "carga": "8h", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/"},
    ],

    "inglês": [
        {"curso": "Inglês para Negócios — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "60h", "nivel": "Curso", "prazo": "medio", "link": "https://www.coursera.org/specializations/english-for-business"},
        {"curso": "Inglês Avançado com foco em Redação Técnica — British Council", "custo": "~R$ 200/mês", "carga": "12 meses", "nivel": "Curso", "prazo": "medio", "link": "https://www.britishcouncil.org.br/"},
        {"curso": "TOEFL / IELTS — preparatório para certificação", "custo": "~US$ 245 (prova)", "carga": "3 meses", "nivel": "Certificação", "prazo": "medio", "link": "https://www.ets.org/toefl"},
    ],
    "espanhol": [
        {"curso": "Espanhol Básico — Duolingo / Busuu", "custo": "Grátis", "carga": "50h", "nivel": "Curso", "prazo": "curto", "link": "https://www.duolingo.com/course/es/pt"},
        {"curso": "Espanhol Intermediário — Instituto Cervantes", "custo": "~R$ 300/mês", "carga": "6 meses", "nivel": "Curso", "prazo": "medio", "link": "https://salvador.cervantes.es/"},
    ],

    "mestrado": [
        {"curso": "Mestrado Profissional em Ciência de Dados — UFBA", "custo": "Grátis (bolsa CAPES: R$ 2.100/mês)", "carga": "24 meses", "nivel": "Pós-graduação", "prazo": "longo", "link": "https://www.ufba.br/pos-graduacao"},
        {"curso": "Mestrado em Economia — UFBA (CAPES 5)", "custo": "Grátis (bolsa CAPES: R$ 2.100/mês)", "carga": "24 meses", "nivel": "Pós-graduação", "prazo": "longo", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "doutorado": [
        {"curso": "Doutorado Stricto Sensu — UFBA", "custo": "Grátis (bolsa CAPES: R$ 3.100/mês)", "carga": "48 meses", "nivel": "Pós-graduação", "prazo": "longo", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "pós-graduação": [
        {"curso": "Especialização em Gestão Pública — UFBA", "custo": "Grátis", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.ufba.br/pos-graduacao"},
        {"curso": "MBA em Data Science — USP/ESALQ (EAD)", "custo": "~R$ 700/mês", "carga": "18 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.esalq.usp.br/"},
        {"curso": "Especialização em Economia do Setor Público — FGV (EAD)", "custo": "~R$ 400/mês", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://educacao-executiva.fgv.br/"},
    ],

    "scrum": [
        {"curso": "PSM I — Professional Scrum Master", "custo": "US$ 150 (prova)", "carga": "20h", "nivel": "Certificação", "prazo": "curto", "link": "https://www.scrum.org/assessments/professional-scrum-master-i-certification"},
    ],
    "pmp": [
        {"curso": "PMP — Project Management Professional", "custo": "US$ 555 (prova)", "carga": "80h", "nivel": "Certificação", "prazo": "medio", "link": "https://www.pmi.org/certifications/project-management-pmp"},
    ],
    "lgpd": [
        {"curso": "LGPD e Proteção de Dados — ENAP", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
    ],

    "gestão pública": [
        {"curso": "Gestão Pública — ENAP", "custo": "Grátis", "carga": "40h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
        {"curso": "Especialização em Políticas Públicas e Gestão Governamental — UFBA", "custo": "Grátis", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "gestão de projetos": [
        {"curso": "Gestão de Projetos — ENAP / FGV Online", "custo": "Grátis", "carga": "30h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "políticas públicas": [
        {"curso": "Avaliação de Políticas Públicas — ENAP/TCU", "custo": "Grátis", "carga": "30h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
        {"curso": "Especialização em Políticas Públicas — UFBA", "custo": "Grátis", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "metodologia científica": [
        {"curso": "Metodologia Científica — Coursera / USP", "custo": "Grátis", "carga": "20h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/learn/metodologia-cientifica"},
    ],
    "análise de dados": [
        {"curso": "Google Data Analytics Certificate — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "180h", "nivel": "Certificado profissional", "prazo": "medio", "link": "https://www.coursera.org/professional-certificates/google-data-analytics"},
        {"curso": "IBM Data Science Professional — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "200h", "nivel": "Certificado profissional", "prazo": "medio", "link": "https://www.coursera.org/professional-certificates/ibm-data-science"},
    ],

    "economia": [
        {"curso": "Economia do Setor Público — ENAP", "custo": "Grátis", "carga": "30h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
        {"curso": "Mestrado em Economia — UFBA (CAPES 5)", "custo": "Grátis (bolsa CAPES: R$ 2.100/mês)", "carga": "24 meses", "nivel": "Mestrado", "prazo": "longo", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "estatística": [
        {"curso": "Estatística para Ciência de Dados — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "40h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/"},
        {"curso": "Especialização em Estatística Aplicada — UFBA", "custo": "Grátis", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "direito": [
        {"curso": "Direito Administrativo para Concursos — ENAP", "custo": "Grátis", "carga": "40h", "nivel": "Curso", "prazo": "curto", "link": "https://www.enap.gov.br/pt/cursos"},
    ],
    "saúde pública": [
        {"curso": "Saúde Pública e Epidemiologia — Coursera", "custo": "Grátis (auxílio financeiro)", "carga": "50h", "nivel": "Curso", "prazo": "curto", "link": "https://www.coursera.org/"},
        {"curso": "Especialização em Saúde Pública — UFBA", "custo": "Grátis", "carga": "12 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://www.ufba.br/pos-graduacao"},
    ],
    "engenharia": [
        {"curso": "Mestrado Profissional em Engenharia Industrial — UFBA (PEI)", "custo": "Grátis", "carga": "24 meses", "nivel": "Mestrado", "prazo": "longo", "link": "https://pei.ufba.br/"},
    ],
    "administração": [
        {"curso": "MBA em Administração Pública — FGV (EAD)", "custo": "~R$ 500/mês", "carga": "18 meses", "nivel": "Pós-graduação", "prazo": "medio", "link": "https://educacao-executiva.fgv.br/"},
    ],
    "ciência da computação": [
        {"curso": "CS50 — Harvard (edX)", "custo": "Grátis (certificado pago)", "carga": "120h", "nivel": "Curso", "prazo": "medio", "link": "https://cs50.harvard.edu/"},
        {"curso": "Mestrado em Ciência da Computação — UFBA (PgCOMP, CAPES 5)", "custo": "Grátis", "carga": "24 meses", "nivel": "Mestrado", "prazo": "longo", "link": "https://pgcomp.ufba.br/"},
    ],
}


PRAZO_LABELS = {
    "curto": {"nome": "Curto Prazo", "icone": "⚡", "descricao": "3 a 6 meses — Cursos e certificações rápidas para resultados imediatos", "cor": "#137333"},
    "medio": {"nome": "Médio Prazo", "icone": "📈", "descricao": "6 a 18 meses — Especializações, MBAs e certificações avançadas", "cor": "#b06000"},
    "longo": {"nome": "Longo Prazo", "icone": "🎓", "descricao": "1 a 3 anos — Mestrados, doutorados e formações estruturantes", "cor": "#1967d2"},
}


def mapear_curso(ferramenta: str) -> list[dict]:
    key = ferramenta.lower().strip()
    if key in CURSO_MAP:
        return CURSO_MAP[key]
    for k, v in CURSO_MAP.items():
        if k in key or key in k:
            return v
    return [{"curso": f"Aprenda {ferramenta} (busque na Udemy/Coursera)", "custo": "Variável", "carga": "Variável", "nivel": "Curso", "prazo": "curto", "link": "https://www.udemy.com/"}]


def gerar_recomendacoes(editais: list, perfil_nome: str) -> dict:
    """Gera recomendações de estudo segmentadas por horizonte temporal."""
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
    mestrado_count = 0
    doutorado_count = 0
    pos_count = 0

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

        if req.get("mestrado"):
            mestrado_count += 1
        if req.get("doutorado"):
            doutorado_count += 1
        if req.get("pos_graduacao"):
            pos_count += 1

        valor = e.get("valor_estimado_num") or 0
        if valor:
            valor_total_oportunidades += valor

    def _classificar_gaps_por_prazo():
        curto, medio, longo = [], [], []

        for ferramenta, count in ferramentas_demand.most_common(15):
            cursos = mapear_curso(ferramenta)
            valor_total = valor_por_ferramenta.get(ferramenta, 0)
            gap = {
                "tipo": "ferramenta",
                "nome": ferramenta,
                "editais": count,
                "impacto_financeiro": round(valor_total, 2) if valor_total else None,
                "cursos": cursos[:3],
            }
            prazos = {c["prazo"] for c in cursos}
            if "curto" in prazos:
                curto.append(gap)
            elif "medio" in prazos:
                medio.append(gap)
            else:
                medio.append(gap)

        for grad, count in graduacoes_demand.most_common(10):
            valor_total = valor_por_graduacao.get(grad, 0)
            cursos = mapear_curso(grad)
            gap = {
                "tipo": "graduacao",
                "nome": grad,
                "editais": count,
                "impacto_financeiro": round(valor_total, 2) if valor_total else None,
                "cursos": cursos[:3],
            }
            prazos = {c.get("prazo", "medio") for c in cursos}
            if "curto" in prazos:
                curto.append(gap)
            elif "medio" in prazos:
                medio.append(gap)
            elif "longo" in prazos:
                longo.append(gap)
            else:
                medio.append(gap)

        for lang, count in idiomas_demand.most_common(4):
            cursos = mapear_curso(lang)
            gap = {
                "tipo": "idioma",
                "nome": lang,
                "editais": count,
                "impacto_financeiro": None,
                "cursos": cursos[:3],
            }
            medio.append(gap)

        if mestrado_count >= 2:
            longo.append({
                "tipo": "formacao",
                "nome": "Mestrado Stricto Sensu",
                "editais": mestrado_count,
                "impacto_financeiro": None,
                "cursos": mapear_curso("mestrado"),
                "nota": f"Exigido ou pontuável em {mestrado_count} editais ({mestrado_count/len(editais)*100:.0f}% do total)",
            })
        if doutorado_count >= 2:
            longo.append({
                "tipo": "formacao",
                "nome": "Doutorado",
                "editais": doutorado_count,
                "impacto_financeiro": None,
                "cursos": mapear_curso("doutorado"),
                "nota": f"Pontuável em {doutorado_count} editais",
            })
        if pos_count >= 2:
            medio.append({
                "tipo": "formacao",
                "nome": "Pós-graduação / Especialização",
                "editais": pos_count,
                "impacto_financeiro": None,
                "cursos": mapear_curso("pós-graduação"),
                "nota": f"Pontuável em {pos_count} editais",
            })

        for lst in [curto, medio, longo]:
            lst.sort(key=lambda g: g["editais"], reverse=True)

        return curto, medio, longo

    curto, medio, longo = _classificar_gaps_por_prazo()

    def _extrair_plano(lst, prazo_key):
        plano = []
        vistos = set()
        for g in lst[:6]:
            for c in g.get("cursos", [])[:1]:
                if (c.get("prazo") == prazo_key or not c.get("prazo")) and c["curso"] not in vistos:
                    vistos.add(c["curso"])
                    plano.append({
                        "gap": g["nome"],
                        "curso": c["curso"],
                        "custo": c["custo"],
                        "carga": c["carga"],
                        "nivel": c.get("nivel", ""),
                        "link": c["link"],
                        "editais_com_gap": g["editais"],
                    })
                    break
        return plano, 0

    plano_curto, _ = _extrair_plano(curto, "curto")
    plano_medio, _ = _extrair_plano(medio, "medio")
    plano_longo, _ = _extrair_plano(longo, "longo")

    custo_curto = sum(int(c["custo"].replace("R$ ", "").replace(".", "").split(" ")[0])
        for c in plano_curto if c["custo"].startswith("R$ ") or c["custo"] == "Grátis") if False else 0

    return {
        "perfil": perfil_nome,
        "descricao": perfil.get("descricao", ""),
        "total_editais_analisados": len(editais),
        "total_editais_compativeis": editais_com_match,
        "valor_total_oportunidades": round(valor_total_oportunidades, 2),
        "periodo_analise": "Últimos 12 meses (dados históricos)",
        "curto_prazo": {
            "gaps": curto,
            "plano": plano_curto,
        },
        "medio_prazo": {
            "gaps": medio,
            "plano": plano_medio,
        },
        "longo_prazo": {
            "gaps": longo,
            "plano": plano_longo,
        },
    }


def gerar_recomendacoes_todos_perfis(editais: list) -> dict:
    perfis = carregar_perfis()
    recomendacoes = {}
    for nome in perfis:
        recomendacoes[nome] = gerar_recomendacoes(editais, nome)
    return recomendacoes
