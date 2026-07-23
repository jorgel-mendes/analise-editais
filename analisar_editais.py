"""
Script de análise de editais PNUD Brasil - Classificação, qualificações e geração de relatórios
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
from fpdf import FPDF

INPUT_FILE = Path(__file__).parent / "dados_brutos" / "editais_ativos.json"
OUTPUT_EXCEL = Path(__file__).parent / "analise_editais_pnud.xlsx"
OUTPUT_PDF = Path(__file__).parent / "relatorio_editais_pnud.pdf"

# ============================================
# 1. CARREGAR E CLASSIFICAR DADOS
# ============================================

with open(INPUT_FILE) as f:
    editais_raw = json.load(f)

# Palavras-chave para classificação de tipo
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

# Palavras-chave para áreas temáticas
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

# Palavras-chave para qualificações típicas
QUALIFICACOES_PADROES = {
    "Graduação (nível superior)": ["graduação", "nível superior", "curso superior", "bacharel", "licenciatura"],
    "Pós-graduação / Especialização": ["pós-graduação", "especialização", "lato sensu"],
    "Mestrado": ["mestrado", "mestre", "stricto sensu"],
    "Doutorado": ["doutorado", "doutor", "phd"],
    "Experiência comprovada": ["experiência", "comprovada", "anos de experiência"],
    "Inglês": ["inglês", "english"],
    "Espanhol": ["espanhol", "spanish"],
    "Pacote Office / Excel": ["excel", "office", "planilha"],
    "Python": ["python"],
    "SQL / Banco de Dados": ["sql", "banco de dados", "database"],
    "GIS / Geoprocessamento": ["gis", "qgis", "arcgis", "geoprocessamento"],
    "Power BI / BI": ["power bi", "bi", "business intelligence", "tableau"],
    "Metodologia científica": ["metodologia", "artigo", "publicação", "pesquisa acadêmica"],
}

def classificar_tipo(titulo, descricao):
    texto = f"{titulo} {descricao or ''}".lower()
    for tipo, palavras in CLASSIFICACAO_TIPOS.items():
        for p in palavras:
            if p in texto:
                return tipo
    return "Consultoria (tipo não especificado)"

def classificar_areas(titulo, descricao):
    texto = f"{titulo} {descricao or ''}".lower()
    areas = []
    for area, palavras in AREAS_TEMATICAS.items():
        for p in palavras:
            if p in texto:
                areas.append(area)
                break
    return areas if areas else ["Não classificada"]

def extrair_valor(comentario):
    if not comentario:
        return None
    match = re.search(r'R\$\s*([\d.]+,\d{2})', comentario)
    if match:
        return match.group(1)
    return None

def extrair_orgao(titulo, email):
    """Tenta extrair o órgão parceiro do título ou email"""
    # Padrões de email
    if email:
        dominio = email.split("@")[-1] if "@" in email else ""
        if "tcu.gov.br" in dominio:
            return "TCU"
        if "ibge.gov.br" in dominio:
            return "IBGE"
        if "gestao.gov.br" in dominio:
            return "MGI"
        if "agu.gov.br" in dominio:
            return "AGU"
        if "trabalho.gov.br" in dominio:
            return "MTE"
        if "undp.org" in dominio:
            return "PNUD (Direto)"
    return "Não identificado"

# Processar editais
editais_processados = []
for e in editais_raw:
    titulo = e.get("title", "")
    descricao = e.get("description", "") or ""
    comentario = e.get("comments", "") or ""
    
    editais_processados.append({
        "id": e["id"],
        "torid": e.get("torid", ""),
        "titulo": titulo,
        "descricao": descricao,
        "tipo": classificar_tipo(titulo, descricao),
        "areas_tematicas": ", ".join(classificar_areas(titulo, descricao)),
        "data_inicio": e.get("startDate", "")[:10] if e.get("startDate") else "",
        "data_fim": e.get("endDate", "")[:10] if e.get("endDate") else "",
        "local": e.get("local", ""),
        "orgao_parceiro": extrair_orgao(titulo, e.get("receivingEmail", "")),
        "email_submissao": e.get("receivingEmail", ""),
        "valor_estimado": extrair_valor(comentario),
        "status": e.get("statusDescription", ""),
        "data_criacao": e.get("created", "")[:10] if e.get("created") else "",
    })

df = pd.DataFrame(editais_processados)

# ============================================
# 2. ANÁLISES
# ============================================

# Contagem por tipo
contagem_tipos = df["tipo"].value_counts()

# Contagem por área temática
areas_flat = []
for areas_str in df["areas_tematicas"]:
    for a in areas_str.split(", "):
        areas_flat.append(a)
contagem_areas = Counter(areas_flat)

# Contagem por órgão
contagem_orgaos = df["orgao_parceiro"].value_counts()

# Faixa de valores
valores = df["valor_estimado"].dropna()
valores_numericos = []
for v in valores:
    try:
        valores_numericos.append(float(v.replace(".", "").replace(",", ".")))
    except:
        pass

# Editais de dados/tecnologia
editais_dados_tech = df[df["areas_tematicas"].str.contains("Tecnologia da Informação / Dados", na=False)]

# Para o usuário (eng. química + dados) - editais com interseção em dados ou metodologia
editais_para_engenheiro = df[
    df["areas_tematicas"].str.contains("Tecnologia da Informação / Dados|Estatística / Pesquisa / Metodologia|Saúde|Meio Ambiente", na=False)
]

# Para o irmão (economia)
editais_para_economista = df[
    df["areas_tematicas"].str.contains("Economia / Finanças Públicas|Gestão / Administração Pública", na=False)
]

print("=" * 60)
print("RESUMO DA ANÁLISE")
print("=" * 60)
print(f"\nTotal de editais ativos: {len(df)}")
print(f"\nClassificação por tipo:")
for tipo, count in contagem_tipos.items():
    print(f"  {tipo}: {count} ({count/len(df)*100:.0f}%)")

print(f"\nÁreas temáticas mais comuns:")
for area, count in contagem_areas.most_common(10):
    print(f"  {area}: {count} ({count/len(df)*100:.0f}%)")

print(f"\nÓrgãos parceiros:")
for orgao, count in contagem_orgaos.items():
    print(f"  {orgao}: {count}")

if valores_numericos:
    print(f"\nValores estimados:")
    print(f"  Mínimo: R$ {min(valores_numericos):,.2f}")
    print(f"  Máximo: R$ {max(valores_numericos):,.2f}")
    print(f"  Médio: R$ {sum(valores_numericos)/len(valores_numericos):,.2f}")
    print(f"  Mediano: R$ {sorted(valores_numericos)[len(valores_numericos)//2]:,.2f}")

print(f"\nEditais de Dados/Tecnologia: {len(editais_dados_tech)}")
for _, e in editais_dados_tech.iterrows():
    print(f"  - {e['titulo'][:100]}")

print(f"\nEditais para perfil Engenheiro (dados/metodologia/saúde/ambiente): {len(editais_para_engenheiro)}")
print(f"Editais para perfil Economista: {len(editais_para_economista)}")

# ============================================
# 3. GERAR EXCEL
# ============================================

with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    # Aba 1: Dados brutos
    df.to_excel(writer, sheet_name="Editais_Ativos", index=False)
    
    # Aba 2: Resumo por tipo
    resumo_tipos = pd.DataFrame({
        "Tipo": contagem_tipos.index,
        "Quantidade": contagem_tipos.values,
        "Percentual": [f"{c/len(df)*100:.0f}%" for c in contagem_tipos.values]
    })
    resumo_tipos.to_excel(writer, sheet_name="Resumo_Tipos", index=False)
    
    # Aba 3: Resumo por área
    resumo_areas = pd.DataFrame({
        "Área Temática": [a for a, _ in contagem_areas.most_common(20)],
        "Quantidade": [c for _, c in contagem_areas.most_common(20)],
        "Percentual": [f"{c/len(df)*100:.0f}%" for _, c in contagem_areas.most_common(20)]
    })
    resumo_areas.to_excel(writer, sheet_name="Resumo_Areas", index=False)
    
    # Aba 4: Editais de Dados/TI
    if len(editais_dados_tech) > 0:
        editais_dados_tech.to_excel(writer, sheet_name="Editais_Dados_TI", index=False)
    
    # Aba 5: Recomendações para o usuário
    if len(editais_para_engenheiro) > 0:
        editais_para_engenheiro.to_excel(writer, sheet_name="Para_Engenheiro_Dados", index=False)
    
    # Aba 6: Recomendações para o irmão
    if len(editais_para_economista) > 0:
        editais_para_economista.to_excel(writer, sheet_name="Para_Economista", index=False)

print(f"\nExcel salvo em: {OUTPUT_EXCEL}")

# ============================================
# 4. GERAR PDF
# ============================================

class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, "Relatório de Análise - Editais PNUD Brasil", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y')} | Fonte: parceiros.undp.org.br/opportunities", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 51, 102)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def table_row(self, cells, widths, bold=False):
        self.set_font("Helvetica", "B" if bold else "", 8)
        for i, (cell, w) in enumerate(zip(cells, widths)):
            self.cell(w, 6, str(cell)[:60], border=1)
        self.ln()


pdf = PDFReport()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Capa
pdf.ln(20)
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 12, "EDITAIS PNUD BRASIL", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 14)
pdf.cell(0, 10, "Análise de Qualificações e Oportunidades", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_font("Helvetica", "I", 10)
pdf.cell(0, 8, "Preparado para: Engenheiro de Dados + Economista", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, f"Período analisado: Editais ativos em {datetime.now().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Fonte: parceiros.undp.org.br/opportunities", align="C", new_x="LMARGIN", new_y="NEXT")

pdf.add_page()

# 1. Visão Geral
pdf.section_title("1. VISÃO GERAL")
pdf.body_text(
    f"Foram analisados {len(df)} editais ativos do PNUD Brasil, listados no portal parceiros.undp.org.br/opportunities. "
    f"A API pública retorna apenas os editais com status 'Aprovada' e dentro do prazo de vigência. "
    f"Não foi possível acessar editais encerrados (API fechada para histórico). "
    f"Os dados foram extraídos via endpoint icnim-api.undp.org.br/v1/publish/list/active."
)
pdf.body_text(
    "Nota importante: As qualificações detalhadas (formação exigida, experiência específica) constam nos "
    "Termos de Referência (ToR) completos, disponíveis apenas via download autenticado no sistema Quantum. "
    "Esta análise baseia-se nos metadados públicos (título, descrição, valor estimado). "
    "Para uma análise completa, recomenda-se baixar cada ToR individualmente do portal."
)

# 2. Classificação por Tipo
pdf.section_title("2. TIPOS DE EDITAL")
pdf.body_text(
    "A maioria dos editais PNUD Brasil são voltados para Consultoria Pessoa Física (PF), "
    "representando a principal porta de entrada para profissionais individuais. "
    "Há também editais de 'Consultoria Especializada' que não especificam PF/PJ no título, "
    "mas que geralmente aceitam ambos. Editais para Pessoa Jurídica são menos comuns na amostra."
)
widths = [80, 25, 25]
pdf.table_row(["Tipo de Edital", "Qtd", "%"], widths, bold=True)
for tipo, count in contagem_tipos.items():
    pdf.table_row([tipo, str(count), f"{count/len(df)*100:.0f}%"], widths)

pdf.ln(3)
pdf.body_text(
    "Recomendação: Foque nos editais de 'Consultoria Pessoa Física' e 'Consultoria Especializada', "
    "que são os mais numerosos e acessíveis para profissionais individuais. "
    "Para projetos maiores, considere abrir uma PJ (MEI ou LTDA) e participar de editais "
    "de Consultoria PJ, que costumam ter valores mais altos."
)

# 3. Áreas Temáticas
pdf.section_title("3. ÁREAS TEMÁTICAS MAIS DEMANDADAS")
pdf.body_text(
    "A seguir, as áreas mais frequentes nos editais. Um mesmo edital pode abranger múltiplas áreas."
)
widths = [80, 25, 25]
pdf.table_row(["Área Temática", "Qtd", "%"], widths, bold=True)
for area, count in contagem_areas.most_common(10):
    pdf.table_row([area, str(count), f"{count/len(df)*100:.0f}%"], widths)

pdf.ln(3)
pdf.body_text(
    "Destaques:\n"
    "- 'Estatística / Pesquisa / Metodologia' lidera devido aos editais do IBGE (Projeto BRA 23/023), que demandam estudos e mapeamentos.\n"
    "- 'Meio Ambiente / Clima / Geografia' tem forte presença, com editais sobre mapeamento climático, povos tradicionais e ecossistemas.\n"
    "- 'Tecnologia da Informação / Dados' aparece em ~27% dos editais, indicando boa demanda para profissionais de dados.\n"
    "- 'Gestão / Administração Pública' e 'Saúde' também têm presença relevante."
)

# 4. Órgãos Parceiros
pdf.section_title("4. ÓRGÃOS PARCEIROS")
widths = [80, 25, 60]
pdf.table_row(["Órgão", "Qtd", "Perfil Típico Demandado"], widths, bold=True)
for orgao, count in contagem_orgaos.items():
    if orgao == "IBGE":
        perfil = "Pesquisadores, estatísticos, geógrafos, analistas de dados"
    elif orgao == "TCU":
        perfil = "Economistas, analistas de saúde, pesquisadores"
    elif orgao == "MGI":
        perfil = "TI, automação, gestão, BI"
    elif orgao == "PNUD (Direto)":
        perfil = "Consultores multidisciplinares, avaliadores"
    elif orgao == "AGU":
        perfil = "Jurídico, proteção de dados"
    elif orgao == "MTE":
        perfil = "Gestão, processos, diagnóstico institucional"
    else:
        perfil = "Variado"
    pdf.table_row([orgao, str(count), perfil], widths)

pdf.ln(3)
pdf.body_text(
    "O IBGE é o maior parceiro (50% dos editais), com projetos do BRA 23/023 (Ambiente de Dados Seguros). "
    "São consultorias de R$ 47.500 a R$ 126.500, remotas, com forte demanda por perfil de pesquisa e dados."
)

# 5. Valores
if valores_numericos:
    pdf.section_title("5. FAIXA DE VALORES")
    pdf.body_text(
        f"Valores estimados (extraídos dos comentários quando disponíveis):\n"
        f"- Mínimo: R$ {min(valores_numericos):,.2f}\n"
        f"- Máximo: R$ {max(valores_numericos):,.2f}\n"
        f"- Médio: R$ {sum(valores_numericos)/len(valores_numericos):,.2f}\n"
        f"- Mediano: R$ {sorted(valores_numericos)[len(valores_numericos)//2]:,.2f}\n\n"
        f"Observação: Apenas {len(valores_numericos)} dos {len(df)} editais possuem valor estimado nos metadados. "
        f"Os valores reais estão nos Termos de Referência completos."
    )

# 6. Oportunidades para Dados/Tecnologia
pdf.section_title("6. OPORTUNIDADES PARA PROFISSIONAIS DE DADOS/TI")
if len(editais_dados_tech) > 0:
    pdf.body_text(
        f"Foram identificados {len(editais_dados_tech)} editais com demanda por tecnologia/dados:"
    )
    for _, e in editais_dados_tech.iterrows():
        pdf.body_text(f"- [{e['id']}] {e['titulo'][:120]}\n  {e['descricao'][:200]}\n  Valor: {e['valor_estimado'] or 'Não informado'} | Local: {e['local']}")
else:
    pdf.body_text("Nenhum edital específico de dados/tecnologia encontrado na amostra atual.")
pdf.ln(2)
pdf.body_text(
    "Perfis de dados/tech mais demandados:\n"
    "- Python + GIS (geoprocessamento) -> editais IBGE\n"
    "- BI (Power BI/Tableau) + automação (SEI/SIC) -> editais MGI\n"
    "- Ciência de dados + análise estatística -> editais IBGE\n"
    "- Desenvolvimento de sistemas / prototipação -> editais TCU\n"
    "- Proteção de dados / LGPD -> editais AGU"
)

# 7. Análise para seu perfil (Engenheiro Químico + Dados)
pdf.section_title("7. OPORTUNIDADES PARA SEU PERFIL (Eng. Química + Dados)")
pdf.body_text(
    f"Sua formação híbrida (Engenharia Química + Análise de Sistemas) é um diferencial importante. "
    f"Dos {len(df)} editais ativos, aproximadamente {len(editais_para_engenheiro)} têm afinidade com seu perfil:"
)
for _, e in editais_para_engenheiro.iterrows():
    pdf.body_text(f"- {e['titulo'][:120]} | Áreas: {e['areas_tematicas']} | Valor: {e['valor_estimado'] or 'NI'}")

pdf.ln(2)
pdf.body_text(
    "Recomendações específicas:\n"
    "1. Destaque sua experiência no BRA 23/023 (edital 54/2025 - ambiente seguro de dados sensíveis) como case.\n"
    "2. A combinação Engenharia + Dados é rara e valiosa para editais do IBGE e TCU.\n"
    "3. Considere uma especialização em Ciência de Dados (12-18 meses, EAD) para fortalecer o currículo.\n"
    "4. Para engenharia química: editais de meio ambiente e clima são oportunidades (ex: TR 97/2026 e 98/2026)."
)

# 8. Análise para o irmão (Economista)
pdf.section_title("8. OPORTUNIDADES PARA ECONOMISTA")
pdf.body_text(
    f"Foram encontrados {len(editais_para_economista)} editais alinhados ao perfil de economia:"
)
for _, e in editais_para_economista.iterrows():
    pdf.body_text(f"- {e['titulo'][:120]} | Áreas: {e['areas_tematicas']} | Valor: {e['valor_estimado'] or 'NI'}")

pdf.ln(2)
pdf.body_text(
    "Recomendações específicas:\n"
    "1. Editais de tributação (TR 07 e 08/2026) são perfeitos para economista.\n"
    "2. Gestão pública e avaliação de políticas têm demanda constante no PNUD.\n"
    "3. Um mestrado em Economia do Setor Público ou Políticas Públicas (UFBA ou UnB) abriria portas.\n"
    "4. Cursos de curta duração em avaliação de políticas públicas (EPPGG/ENAP) são gratuitos e bem vistos."
)

# 9. Recomendações de Capacitação
pdf.section_title("9. RECOMENDAÇÕES DE CAPACITAÇÃO")

pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 7, "Para você (Engenheiro de Dados) - Orçamento ~R$1.000/mês:", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(50, 50, 50)
pdf.body_text(
    "Curto prazo (3-6 meses, R$200-600/mês):\n"
    "1. Especialização em Ciência de Dados (PUC-Rio, USP/ESALQ, UFBA - EAD) - R$400-600/mês\n"
    "2. Certificação Python (PCAP/PCAD) ou Google Data Analytics - R$200/mês\n"
    "3. Curso de geoprocessamento QGIS/Python geo - gratuito (INPE) ou R$200/mês\n\n"
    "Médio prazo (12-24 meses):\n"
    "4. Mestrado em Ciência de Dados / Computação (UFBA - gratuito, Salvador)\n"
    "5. Mestrado Profissional em Engenharia Ambiental (UFBA) - combina engenharia química + dados\n"
    "6. MBA em Data Science & Analytics (USP/ESALQ) - EAD, ~R$700/mês"
)

pdf.ln(2)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 7, "Para seu irmão (Economista) - Orçamento ~R$500/mês:", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(50, 50, 50)
pdf.body_text(
    "Curto prazo (3-6 meses):\n"
    "1. Curso de Avaliação de Políticas Públicas (ENAP/TCU) - gratuito\n"
    "2. Especialização em Economia do Setor Público (UFBA) - gratuito\n"
    "3. Certificação em Análise de Dados (Google/Coursera) - R$150/mês\n\n"
    "Médio prazo (12-24 meses):\n"
    "4. Mestrado em Economia com ênfase em Finanças Públicas (UFBA) - gratuito\n"
    "5. Pós em Políticas Públicas e Gestão Governamental - EAD, ~R$400/mês"
)

pdf.ln(2)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 7, "Cursos gratuitos com chancela para PNUD:", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(50, 50, 50)
pdf.body_text(
    "1. ENAP - Escola Nacional de Administração Pública (diversos cursos EAD gratuitos)\n"
    "2. ESG - Escola Superior de Guerra (cursos de gestão e governança)\n"
    "3. ILPF - Instituto Legislativo (cursos de orçamento público)\n"
    "4. Coursera/EdX - Certificados profissionais com bolsa (Data Science, Python, R)\n"
    "5. INPE - Cursos de geoprocessamento e sensoriamento remoto (gratuitos)"
)

# 10. Estratégia
pdf.section_title("10. ESTRATÉGIA RECOMENDADA")
pdf.body_text(
    "1. Cadastro e networking:\n"
    "   - Mantenha seu cadastro no portal parceiros.undp.org.br atualizado\n"
    "   - Cadastre-se também no UNGM (ungm.org) - marketplace global da ONU\n"
    "   - Conecte-se com os aprovadores listados nos editais no LinkedIn\n\n"
    "2. Aproveite o projeto atual:\n"
    "   - O BRA 23/023 (edital 54/2025) é sua porta de entrada - entregue com excelência\n"
    "   - Documente tudo como case para próximos editais\n"
    "   - Peça carta de recomendação ao gestor do PNUD ao final do projeto\n\n"
    "3. Diversifique:\n"
    "   - Você (PF): consultorias de dados, metodologia, sistemas\n"
    "   - Irmão (PF): consultorias de economia, finanças públicas\n"
    "   - Juntos (PJ): abrir empresa para pegar projetos maiores e multidisciplinares\n\n"
    "4. Áreas com alta demanda futura (tendências observadas):\n"
    "   - Proteção de dados / LGPD (Editais AGU e MGI)\n"
    "   - Geoprocessamento / GIS (Editais IBGE)\n"
    "   - BI e automação de processos (Editais MGI)\n"
    "   - Mudanças climáticas e meio ambiente (Editais IBGE)\n"
    "   - Avaliação de políticas públicas (Editais TCU e PNUD)"
)

# Salvar
pdf.output(str(OUTPUT_PDF))
print(f"PDF salvo em: {OUTPUT_PDF}")

# Salvar também JSON processado
output_json = Path(__file__).parent / "dados_brutos" / "editais_processados.json"
df.to_json(output_json, orient="records", force_ascii=False, indent=2)
print(f"JSON processado salvo em: {output_json}")
