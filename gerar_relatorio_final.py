"""
Gerar relatorio completo com roadmap detalhado de capacitacao
Contexto: Engenheiro Quimico + Dados na FIEB, com multiplas formacoes em andamento
"""
import json, re
from datetime import datetime
from pathlib import Path
from collections import Counter
from fpdf import FPDF
import pandas as pd

INPUT_JSON = Path(__file__).parent / "dados_brutos" / "editais_ativos.json"
QUALS_JSON = Path(__file__).parent / "dados_brutos" / "qualificacoes_extraidas.json"
OUTPUT_PDF = Path(__file__).parent / "relatorio_editais_pnud.pdf"
OUTPUT_EXCEL = Path(__file__).parent / "analise_editais_pnud.xlsx"

with open(INPUT_JSON) as f:
    editais = json.load(f)
with open(QUALS_JSON) as f:
    qualificacoes = json.load(f)

# ============================================
# AGREGACOES
# ============================================
ALL_GRADUACOES_VALIDAS = [
    "engenharia", "economia", "estatística", "geografia", "direito",
    "ciências sociais", "ciência da computação", "engenharia de software",
    "sistemas de informação", "tecnologia da informação", "análise de sistemas",
    "engenharia da computação", "ciência de dados", "inteligência artificial",
    "arquitetura", "história", "comunicação", "administração",
    "políticas públicas", "gestão pública", "matemática", "física",
    "biologia", "ecologia", "engenharia química", "engenharia ambiental",
    "saúde pública", "enfermagem", "medicina", "ciências contábeis",
    "biblioteconomia", "arquivologia", "antropologia", "sociologia",
    "ciência política", "relações internacionais", "urbanismo",
    "geologia", "química",
]
ALL_FERRAMENTAS_VALIDAS = [
    "power bi", "power automate", "power query", "dax", "power platform",
    "sharepoint", "microsoft 365", "outlook", "teams", "planner",
    "python", "r", "sql", "excel", "tableau", "qgis", "arcgis",
    "google earth engine", "stata", "spss", "sas", "matlab",
    "git", "docker", "azure", "aws", "google cloud",
    "sei", "sic", "project online", "dataverse",
]

graduacao_counter = Counter()
ferramentas_counter = Counter()
for q in qualificacoes:
    for g in q.get("graduacao", []):
        if g in ALL_GRADUACOES_VALIDAS:
            graduacao_counter[g] += 1
    for f in q.get("ferramentas", []):
        if f in ALL_FERRAMENTAS_VALIDAS:
            ferramentas_counter[f] += 1

mestrado_count = sum(1 for q in qualificacoes if q.get("mestrado"))
doutorado_count = sum(1 for q in qualificacoes if q.get("doutorado"))
pos_count = sum(1 for q in qualificacoes if q.get("pos_graduacao"))

exp_anos = [q["anos_experiencia"] for q in qualificacoes if q.get("anos_experiencia")]
exp_counter = Counter(exp_anos)

idiomas_counter = Counter()
for q in qualificacoes:
    for lang in q.get("idiomas", []):
        idiomas_counter[lang] += 1

valores_totais = []
# Extrair valor TOTAL do contrato (nao parcelas)
# Prioridade: texto do TOR > comentario de aprovacao
TORS_DIR = Path(__file__).parent / "dados_brutos" / "tors"

def extrair_valor_total(comentario, torid):
    """Extrai o valor TOTAL do contrato, evitando parcelas."""
    valores_encontrados = []

    # 1. Buscar no texto do TOR (mais confiavel para o total)
    tor_text_file = TORS_DIR / f"{torid}_texto.txt"
    if tor_text_file.exists():
        tor_text = tor_text_file.read_text()
        # "Valor da contratacao: R$ 170.000,00" ou "Total do perfil ... R$ 170.000,00"
        for padrao in [
            r'Valor\s+da\s+contrata[cç][aã]o\s*:?\s*R\$\s*([\d.]+,\d{2})',
            r'Total\s+do\s+perfil\s+.*?R\$\s*([\d.]+,\d{2})',
            r'valor\s+total\s+de\s+R\$\s*([\d.]+,\d{2})',
        ]:
            m = re.search(padrao, tor_text, re.IGNORECASE)
            if m:
                try:
                    v = float(m.group(1).replace(".", "").replace(",", "."))
                    if v > 1000:  # valor total e sempre > R$ 1000
                        valores_encontrados.append(v)
                        break
                except:
                    pass

    # 2. Buscar no comentario "valor total de R$ X"
    if comentario:
        m = re.search(r'valor\s+total\s+de\s+R\$\s*([\d.]+,\d{2})', comentario, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1).replace(".", "").replace(",", "."))
                if v > 1000:
                    valores_encontrados.append(v)
            except:
                pass

    # 3. Fallback: ultimo valor R$ no comentario (geralmente o total)
    if not valores_encontrados and comentario:
        all_values = re.findall(r'R\$\s*([\d.]+,\d{2})', comentario)
        if all_values:
            try:
                v = float(all_values[-1].replace(".", "").replace(",", "."))
                if v > 1000:
                    valores_encontrados.append(v)
            except:
                pass

    return max(valores_encontrados) if valores_encontrados else None

for e in editais:
    comentario = e.get("comments", "") or ""
    torid = str(e.get("torid", ""))
    valor = extrair_valor_total(comentario, torid)
    if valor:
        valores_totais.append(valor)

# Mapa torid -> valor total para uso nas secoes
valor_total_por_torid = {}
for e in editais:
    torid = str(e.get("torid", ""))
    comentario = e.get("comments", "") or ""
    v = extrair_valor_total(comentario, torid)
    if v:
        valor_total_por_torid[torid] = v

editais_dados = [q for q in qualificacoes if any(
    f in q.get("ferramentas", []) for f in ["power bi", "power automate", "python", "sql", "sharepoint", "qgis"]
)]
editais_economista = [q for q in qualificacoes if any(
    g in q.get("graduacao", []) for g in ["economia", "políticas públicas", "gestão pública"]
)]

orgaos = Counter()
for e in editais:
    email = e.get("receivingEmail", "")
    if "ibge" in email: orgaos["IBGE"] += 1
    elif "tcu" in email: orgaos["TCU"] += 1
    elif "gestao.gov" in email: orgaos["MGI"] += 1
    elif "agu" in email: orgaos["AGU"] += 1
    elif "trabalho" in email: orgaos["MTE"] += 1
    elif "undp" in email: orgaos["PNUD (Direto)"] += 1
    else: orgaos["Outros"] += 1

# ============================================
# PDF
# ============================================
class PDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_left_margin(15)
        self.set_right_margin(15)
        self.set_top_margin(15)
        self.W = 210 - 15 - 15  # usable width = 180mm

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(0, 51, 102)
            self.cell(self.W, 4, "Editais PNUD Brasil - Relatorio de Analise e Roadmap", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(0, 51, 102)
            self.set_line_width(0.2)
            self.line(self.l_margin, self.get_y() + 1, self.l_margin + self.W, self.get_y() + 1)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 6)
        self.set_text_color(140)
        self.cell(self.W, 6, f"Pagina {self.page_no()}/{{nb}} | {datetime.now().strftime('%d/%m/%Y')} | parceiros.undp.org.br", align="C")

    def title1(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(self.W, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y() + 1, self.l_margin + self.W, self.get_y() + 1)
        self.ln(4)

    def title2(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 70, 130)
        self.cell(self.W, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def title3(self, text):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(80, 80, 80)
        self.cell(self.W, 5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(60, 60, 60)
        self.multi_cell(self.W, 4, text, align="L")
        self.ln(1)

    def bold_body(self, text):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(60, 60, 60)
        self.multi_cell(self.W, 4, text, align="L")
        self.ln(1)

    def bullet(self, text, indent=5):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(60, 60, 60)
        x0 = self.l_margin + indent
        self.set_x(x0)
        self.cell(3, 4, "-")
        self.set_x(x0 + 4)
        self.multi_cell(self.W - indent - 4, 4, text, align="L")
        self.ln(0.2)

    def numbered(self, num, text, indent=5):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(60, 60, 60)
        x0 = self.l_margin + indent
        self.set_x(x0)
        self.cell(5, 4, f"{num}.")
        self.set_x(x0 + 6)
        self.multi_cell(self.W - indent - 6, 4, text, align="L")
        self.ln(0.2)

    def table(self, headers, rows, col_widths=None):
        """Smart table with automatic width calculation and text wrapping."""
        n = len(headers)
        if col_widths is None:
            col_widths = [self.W // n] * n
        # Normalize to ensure sum equals self.W
        total = sum(col_widths)
        col_widths = [w * self.W / total for w in col_widths]

        # Header
        self.set_font("Helvetica", "B", 6.5)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self._table_row(headers, col_widths, fill=True, bold=True)
        self.ln(0)

        # Body
        self.set_font("Helvetica", "", 6.5)
        for i, row in enumerate(rows):
            if i % 2 == 0:
                self.set_fill_color(242, 246, 252)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_text_color(60, 60, 60)
            self._table_row(row, col_widths, fill=True, bold=False)
            self.ln(0)
        self.ln(3)

    def _table_row(self, cells, col_widths, fill=False, bold=False):
        """Draw a table row with automatic cell height based on longest text."""
        # Calculate max height needed
        cell_texts = [str(c) if c else "" for c in cells]
        line_height = 3.5
        max_lines = 1
        for i, text in enumerate(cell_texts):
            # Estimate lines needed
            char_width = self.get_string_width("a")
            chars_per_line = max(1, int((col_widths[i] - 2) / char_width))  # -2 for padding
            lines = max(1, -(-len(text) // chars_per_line))  # ceiling division
            max_lines = max(max_lines, min(lines, 8))  # cap at 8 lines

        row_height = max_lines * line_height + 2
        y_before = self.get_y()

        # Check page break
        if y_before + row_height > self.h - self.b_margin:
            self.add_page()
            y_before = self.get_y()

        # Draw cells
        x_start = self.get_x()
        for i, text in enumerate(cell_texts):
            x_pos = x_start + sum(col_widths[:i])
            self.set_xy(x_pos, y_before)
            # Draw cell background and border
            self.set_fill_color(242 if not bold and i % 2 == 0 else 255)
            if fill:
                self.set_fill_color(0, 51, 102) if bold else None
            self.rect(x_pos, y_before, col_widths[i], row_height, "D")
            if fill and bold:
                self.set_fill_color(0, 51, 102)
                self.rect(x_pos, y_before, col_widths[i], row_height, "F")
            elif fill:
                base_fill = self.fill_color
                self.rect(x_pos, y_before, col_widths[i], row_height, "F")
            # Write text
            self.set_xy(x_pos + 1, y_before + 1)
            self.set_text_color(255 if bold else 60)
            self.multi_cell(col_widths[i] - 2, line_height, text, align="L")

        self.set_xy(x_start, y_before + row_height)


pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=18)

# ============================================
# CAPA
# ============================================
pdf.add_page()
pdf.ln(25)
pdf.set_font("Helvetica", "B", 26)
pdf.set_text_color(0, 51, 102)
pdf.cell(0, 14, "EDITAIS PNUD BRASIL", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)
pdf.set_font("Helvetica", "", 16)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 10, "Analise de Qualificacoes e Roadmap de Capacitacao", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)
pdf.set_draw_color(0, 51, 102)
pdf.set_line_width(0.5)
pdf.line(pdf.l_margin + 30, pdf.get_y(), pdf.l_margin + pdf.W - 30, pdf.get_y())
pdf.ln(10)
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 7, f"{len(editais)} editais ativos analisados | {len(qualificacoes)} TORs processados", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, f"Dados extraidos dos PDFs originais em {datetime.now().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "Fonte: parceiros.undp.org.br/opportunities", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, "Preparado para: Engenheiro de Dados (FIEB) + Economista (Irmao)", align="C", new_x="LMARGIN", new_y="NEXT")

# ============================================
# SUMARIO EXECUTIVO
# ============================================
pdf.add_page()
pdf.title1("SUMARIO EXECUTIVO")
pdf.body(
    f"Este relatorio analisa {len(editais)} editais ativos do PNUD Brasil com base nos Termos de Referencia "
    f"(ToR) completos, baixados e processados automaticamente. Diferentemente de analises baseadas apenas em "
    f"metadados, esta versao extrai qualificacoes obrigatorias, desejaveis, ferramentas exigidas e faixas "
    f"salariais diretamente dos PDFs oficiais. "
    f"Inclui um roadmap detalhado de capacitacao alinhado ao contexto academico e profissional do usuario."
)
pdf.bold_body("PRINCIPAIS ACHADOS:")
pdf.bullet(f"Mestrado exigido ou pontuavel em {mestrado_count}/{len(qualificacoes)} editais ({mestrado_count/len(qualificacoes)*100:.0f}%). Doutorado em {doutorado_count} ({doutorado_count/len(qualificacoes)*100:.0f}%).")
pdf.bullet(f"Power BI: {ferramentas_counter.get('power bi', 0)} editais. Python: {ferramentas_counter.get('python', 0)}. QGIS/ArcGIS: {ferramentas_counter.get('qgis', 0)}/{ferramentas_counter.get('arcgis', 0)}.")
pdf.bullet(f"Valor medio dos contratos: R$ {sum(valores_totais)/len(valores_totais):,.2f}" if valores_totais else "Valores entre R$ 47.500 e R$ 170.000")
pdf.bullet(f"Editais com perfil de dados/TI: {len(editais_dados)}. Economia/gestao: {len(editais_economista)}.")
pdf.bullet("63% remotos. Maioria com disponibilidade para viagens curtas.")
pdf.bullet("IBGE domina com 14 editais (Projeto BRA 23/023 - Ambiente de Dados Seguros).")

# ============================================
# 1. PANORAMA
# ============================================
pdf.add_page()
pdf.title1("1. PANORAMA DOS EDITAIS ATIVOS")

pdf.title2("1.1 Orgaos Parceiros")
pdf.table(
    ["Orgao", "Qtd", "Perfil Predominante", "Faixa de Valor"],
    [
        ["IBGE", "14", "Pesquisadores, estatisticos, geografos", "R$ 47.500 - R$ 126.500"],
        ["TCU", "5", "Economistas, saude, pesquisadores", "R$ 2.250 - R$ 24.999"],
        ["PNUD Direto", "3", "Consultores multidisciplinares", "NI"],
        ["MGI", "2", "TI, BI, automacao, gestao", "R$ 168.000 - R$ 170.000"],
        ["AGU", "1", "Juridico, protecao de dados", "R$ 10.714"],
        ["MTE", "1", "Gestao, processos", "R$ 7.417"],
    ],
    [32, 13, 80, 65]
)

pdf.title2("1.2 Exigencias Academicas (presentes nos TORs)")
pdf.table(
    ["Nivel Academico", "Qtd Editais", "%", "Observacao"],
    [
        ["Graduacao (obrigatorio)", str(len(qualificacoes)), "100%", "Todos os editais exigem nivel superior"],
        ["Pos-graduacao / Especializacao", str(pos_count), f"{pos_count/len(qualificacoes)*100:.0f}%", "Diferencial pontuavel na maioria"],
        ["Mestrado (exigido ou pontua)", str(mestrado_count), f"{mestrado_count/len(qualificacoes)*100:.0f}%", "58% dos editais. Pode ser obrigatorio ou desejavel"],
        ["Doutorado (exigido ou pontua)", str(doutorado_count), f"{doutorado_count/len(qualificacoes)*100:.0f}%", "50% dos editais. Especialmente IBGE e TCU"],
    ],
    [52, 25, 18, 95]
)

pdf.title2("1.3 Ferramentas Mais Demandadas")
ferr_rows = [[f, str(c)] for f, c in ferramentas_counter.most_common(12)]
pdf.table(["Ferramenta / Tecnologia", "Qtd Editais"], ferr_rows, [110, 80])
pdf.body("Nota: R e SAS tem contagem alta por aparecerem como contexto nos TORs do IBGE, nao necessariamente como requisito obrigatorio. Python (4), Power BI (2), QGIS (1) e ArcGIS (1) sao demandas explicitas.")

# ============================================
# 2. QUALIFICACOES POR ORGAO
# ============================================
pdf.add_page()
pdf.title1("2. QUALIFICACOES DETALHADAS POR ORGAO")

pdf.title2("2.1 IBGE (14 editais) - Projeto BRA 23/023")
pdf.body("Os editais do IBGE formam o maior bloco. Sao consultorias de pesquisa aplicada, com entregas de relatorios tecnicos e estudos.")
pdf.bold_body("Padrao de qualificacao IBGE:")
pdf.bullet("Graduacao em area especifica (varia por edital) + Mestrado ou Doutorado (desejavel/obrigatorio)")
pdf.bullet("Experiencia de 2-5 anos em pesquisa, analise de dados ou area tematica")
pdf.bullet("Ferramentas: depende do tema. Python+ GIS no TR 90/2026. R e SAS mencionados como contexto.")
pdf.bullet("Valores: R$ 47.500 a R$ 126.500 por contrato")
pdf.bullet("Todos remotos, com possibilidade de viagens curtas")
pdf.bullet("Submissao: projetos.especiais@ibge.gov.br")

pdf.title2("2.2 TCU (5 editais) - PRODOC BRA 23/022")
pdf.body("Consultorias para estudos tecnicos em saude e tributacao.")
pdf.bold_body("Padrao TCU:")
pdf.bullet("Graduacao em area especifica. Mestrado/Doutorado fortemente valorizados.")
pdf.bullet("Perfis: saude (TR 04-06), economia/tributacao (TR 07-08)")
pdf.bullet("Submissao: AudSaude@tcu.gov.br (saude) ou segecex-assessoria@tcu.gov.br (tributacao)")

pdf.title2("2.3 MGI (2 editais) - Editais 10 e 11/2026")
pdf.body("Consultorias de TI e gestao. Sao as unicas que exigem ferramentas Microsoft especificas.")
pdf.bold_body("Edital 10/2026 - Gestao do Conhecimento:")
pdf.bullet("Foco: metodologia de dimensionamento da forca de trabalho")
pdf.bullet("Valor total: R$ 168.000 | Prazo: 19/05/2026")
pdf.bullet("Submissao: prodoc.mgi@gestao.gov.br")

pdf.bold_body("Edital 11/2026 - BI + Power Automate (DESTAQUE):")
pdf.bullet("Foco: Power BI, Power Automate, SharePoint, Microsoft 365")
pdf.bullet("Valor total: R$ 170.000 (7 produtos em 340 dias)")
pdf.bullet("Requisito: 5 anos em BI, Power Automate e SharePoint")
pdf.bullet("Prazo: 20/05/2026 | Submissao: prodoc.mgi@gestao.gov.br")

# ============================================
# 3. OPORTUNIDADES DADOS/TI
# ============================================
pdf.add_page()
pdf.title1("3. OPORTUNIDADES PARA DADOS E TECNOLOGIA")
pdf.body(f"{len(editais_dados)} editais com demanda clara por profissionais de dados/tecnologia:")

for q in editais_dados:
    titulo = q.get("titulo", "")
    ferrs = ", ".join([f for f in q.get("ferramentas", []) if f in ALL_FERRAMENTAS_VALIDAS][:5])
    torid = q.get("torid", "")
    valor_total = valor_total_por_torid.get(torid)
    pdf.bold_body(f"* {titulo}")
    if ferrs:
        pdf.bullet(f"Ferramentas: {ferrs}")
    if valor_total:
        pdf.bullet(f"Valor total do contrato: R$ {valor_total:,.2f}")
    pdf.bullet(f"Local: {q.get('local', 'NI')} | Prazo: {q.get('data_fim', 'NI')}")
    pdf.ln(1.5)

pdf.title2("Resumo para amigos de dados/TI:")
pdf.bullet("Power BI + Power Automate + SharePoint: editais MGI (10 e 11/2026)")
pdf.bullet("Python + GIS + geoprocessamento: TR 90/2026 (IBGE, R$ 91.500)")
pdf.bullet("Protecao de Dados / LGPD: BRA20/023 (AGU)")
pdf.bullet("Python + analise estatistica: diversos editais IBGE")
pdf.bullet("BI + automação SEI/SIC: Edital 11/2026 (MGI)")

# ============================================
# 4. OPORTUNIDADES PARA OS PERFIS
# ============================================
pdf.add_page()
pdf.title1("4. OPORTUNIDADES PARA SEUS PERFIS")

pdf.title2("4.1 Para voce (Engenheiro Quimico + Dados, FIEB)")
pdf.body("Seu perfil combina tres dimensoes valiosas para editais PNUD:")
pdf.bullet("1. Dados publicos e economicos (experiencia FIEB) -> editais IBGE e TCU")
pdf.bullet("2. Engenharia + TI (formacao hibrida) -> editais de sistemas e metodologia")
pdf.bullet("3. LGPD e protecao de dados (pos i9) -> editais AGU e de dados sensiveis")

pdf.bold_body("Editais com melhor encaixe HOJE:")
pdf.bullet("TR 90/2026 (IBGE) - Python + GIS + dados -> R$ 91.500 - ate 18/05")
pdf.bullet("Edital 11/2026 (MGI) - BI + Power Automate -> R$ 170.000 - ate 20/05")
pdf.bullet("TR 115/2026 (IBGE) - Era Digital, disseminacao de dados -> R$ 126.500 - ate 18/05")
pdf.bullet("BRA20/023 (AGU) - Privacidade e protecao de dados -> ate 18/05")
pdf.bullet("TR 04/2026 (TCU) - Estudo de viabilidade, requisitos, prototipacao de sistema -> ate 17/05")

pdf.title2("4.2 Para seu irmao (Economista)")
pdf.body(f"{len(editais_economista)} editais com afinidade direta a Economia:")
for q in editais_economista:
    titulo = q.get("titulo", "")
    torid = q.get("torid", "")
    valor_total = valor_total_por_torid.get(torid)
    pdf.bullet(f"{titulo}")
    if valor_total:
        pdf.bullet(f"  Valor total do contrato: R$ {valor_total:,.2f} | Prazo: {q.get('data_fim', 'NI')}", indent=10)
    else:
        pdf.bullet(f"  Valor: consultar TOR | Prazo: {q.get('data_fim', 'NI')}", indent=10)

pdf.ln(2)
pdf.bold_body("Melhores para economista HOJE:")
pdf.bullet("TR 07/2026 (TCU) - Incidencia distributiva da carga tributaria - ate 24/05")
pdf.bullet("TR 08/2026 (TCU) - Tributacao otima no bem-estar social - ate 24/05")
pdf.bullet("Editais de politicas publicas e gestao (futuros)")

# ============================================
# 5. CONTEXTO ATUAL DE FORMACAO
# ============================================
pdf.add_page()
pdf.title1("5. SEU CONTEXTO ATUAL DE FORMACAO")

pdf.body("Antes de definir o roadmap, e importante mapear o que voce ja tem e como cada credencial se posiciona no mercado PNUD.")

pdf.title2("5.1 Formacoes Concluidas ou em Andamento")
pdf.table(
    ["Formacao", "Area", "Conclusao", "Peso em Editais PNUD", "Observacao"],
    [
        ["Graduacao Eng. Quimica", "Engenharia", "Concluida", "MEDIO", "Aceita em editais de engenharia/ambiental. Limitada para TI."],
        ["Graduacao Analise de Sistemas", "TI", "Concluida", "ALTO", "Aceita em todos os editais de TI/Dados. Essencial."],
        ["Masters Software Eng. (Quantic)", "TI", "2026", "BAIXO (nao conta como mestrado BR)", "Nao reconhecido como stricto sensu no Brasil. Vale como especializacao."],
        ["Pos Industria 4.0", "Eng/TI", "2028", "MEDIO-ALTO", "Pontua como pos-graduacao. Tema relevante para governo digital."],
        ["Pos LGPD (i9)", "Direito Digital", "2026", "ALTO", "Diretamente aplicavel a editais de protecao de dados. Case: BRA 23/023."],
        ["Pos Gestao Publica (i9)", "Gestao", "2027", "ALTO", "Abre portas para editais de gestao, politicas publicas e administracao."],
    ],
    [38, 28, 22, 42, 60]
)

pdf.title2("5.2 Forcas e Gaps Atuais")
pdf.bold_body("Forcas:")
pdf.bullet("Dupla graduacao (Engenharia + TI) = perfil raro e valorizado")
pdf.bullet("Experiencia pratica em dados publicos (FIEB) = case concreto")
pdf.bullet("Experiencia previa PNUD (BRA 23/023, edital 54/2025) = diferencial competitivo enorme")
pdf.bullet("Pos LGPD + Pos Gestao Publica = cobre areas de alta demanda")
pdf.bullet("Ingles (Quantic) = util para editais internacionais e documentos ONU")

pdf.bold_body("Gaps a preencher:")
pdf.bullet("Falta mestrado stricto sensu reconhecido no Brasil (58% dos editais pontuam)")
pdf.bullet("Falta certificacoes Microsoft (Power BI PL-300, Azure) para editais MGI")
pdf.bullet("Ferramentas de BI praticas (Power BI, Tableau) para alem da teoria")
pdf.bullet("Geoprocessamento (QGIS/ArcGIS) para editais IBGE")

pdf.title2("5.3 Perfil do Irmao (Economista + Tecnologo em Analise de Sistemas)")
pdf.body(
    "Seu irmao possui graduacao em Economia e Tecnologo em Analise de Sistemas (concluido). "
    "Esta combinacao e extremamente poderosa: ele entende macroeconomia e politicas publicas "
    "E sabe programar, analisar dados e trabalhar com ferramentas de TI. "
    "Isso transforma o perfil dele de 'so economista' para economista com stack tecnica, "
    "abrindo muito mais portas tanto no PNUD quanto no mercado privado."
)

pdf.bold_body("Forcas do perfil dele:")
pdf.bullet("Economia + TI = profissional hibrido raro, capaz de unir analise economica com implementacao tecnica")
pdf.bullet("Pode atuar tanto em editais de economia (TCU, PNUD) quanto de dados (IBGE, MGI)")
pdf.bullet("Tecnologo em Analise de Sistemas atende ao requisito de graduacao em TI de varios editais")
pdf.bullet("Disponibilidade para viagens (diferencial para projetos com campo)")
pdf.bullet("Acesso a UFBA para pos-graduacao gratuita em Salvador")

pdf.bold_body("Gaps do perfil dele:")
pdf.bullet("Sem experiencia previa com PNUD/ONU (o maior gap - projetos ONU valorizam muito isso)")
pdf.bullet("Sem pos-graduacao (especializacao ou mestrado) - necessario para pontuar nos editais")
pdf.bullet("Sem certificacoes de ferramentas (Power BI, SQL, Python) que comprovem a stack tecnica")
pdf.bullet("Sem portfolio publico de projetos de dados/economia (GitHub, cases)")

pdf.bold_body("Estrategia para o irmao: duas trilhas paralelas ate 2028")
pdf.body(
    "Como ele esta procurando emprego agora, o roadmap dele tem dois caminhos que NAO sao excludentes - "
    "ele pode seguir ambos simultaneamente:\n"
    "TRILHA A: Emprego em Salvador ou remoto (curto prazo, 2026-2027)\n"
    "TRILHA B: Mestrado com bolsa na UFBA (medio prazo, 2027-2029)\n"
    "Idealmente, ele consegue um emprego em 2026/2027 E inicia o mestrado em 2027. "
    "Se conseguir bolsa CAPES (R$ 2.100/mes), pode inclusive se dedicar integralmente ao mestrado."
)

# ============================================
# 6. ROADMAP DE CAPACITACAO
# ============================================
pdf.add_page()
pdf.title1("6. ROADMAP DE CAPACITACAO 2026-2029")
pdf.body(
    "Este roadmap considera seu orcamento (~R$ 1.000/mes), sua localizacao (Salvador/BA, com acesso a UFBA), "
    "e suas formacoes em andamento. O objetivo e voce conseguir 1 edital em 2027 e, junto com seu irmao, "
    "2 editais simultaneos em 2028/2029. Cada etapa indica o que fazer, custo estimado e quais editais "
    "aquela formacao destrava."
)

# --- FASE 1: 2026 (agora) ---
pdf.title2("6.1 FASE 1: Imediato (Mai-Dez 2026) - Preparar o terreno")

pdf.title3("Para voce (orcamento: R$ 0-300/mes nesta fase):")
pdf.bullet("Concluir Masters Quantic + Pos LGPD (i9) - sem custo adicional, ja estao pagos")
pdf.bullet("Certificacao Microsoft PL-300 (Power BI Data Analyst) - gratuito (MS Learn) + R$ 300 a prova")
pdf.bullet("Certificacao Microsoft PL-900 (Power Platform Fundamentals) - gratuito (MS Learn) + R$ 210 a prova")
pdf.bullet("Curso QGIS basico (INPE) - gratuito, EAD. 40h. Abre editais de geoprocessamento.")
pdf.bullet("Montar portfolio: GitHub com scripts Python do projeto atual (anonimizado) + dashboards Power BI")
pdf.bullet("Atualizar curriculo formato ONU (modelo P11). Destacar projeto BRA 23/023 na primeira pagina.")

pdf.title3("Para o irmao: TRILHA A - Emprego em Salvador/Remoto (orcamento: R$ 0-200/mes)")
pdf.bullet("Certificacao Google Data Analytics (Coursera) - R$ 150/mes, 3-6 meses. Primeira credencial tecnica.")
pdf.bullet("SQL Fundamentals + Excel Avancado (Udemy) - R$ 30 cada. Essenciais para vagas de analista.")
pdf.bullet("Power BI basico (MS Learn) - gratuito. Complementa a stack de dados.")
pdf.bullet("Montar LinkedIn com palavras-chave: Python, SQL, Power BI, Economia, Analise de Dados.")
pdf.bullet("Vagas alvo em Salvador/remoto: analista de dados no mercado financeiro (bancos, fintechs), instituicoes de pesquisa (IEL/FIEB, SEI-BA, IBGE), consultorias economicas, programas de trainee (bancos, BNDES).")
pdf.bullet("Onde procurar: LinkedIn (filtro 'remoto' + 'Salvador'), Gupy, Vagas.com, sites de trainee.")

pdf.title3("Para o irmao: TRILHA B - Mestrado com bolsa (orcamento: R$ 0)")
pdf.bullet("Mestrado em Economia (UFBA) - gratuito, conceito CAPES 5. Processo seletivo anual (inscricao 2o sem 2026, inicio 2027.1).")
pdf.bullet("OU: Mestrado em Ciencia da Computacao (UFBA) se quiser puxar mais para o lado tech.")
pdf.bullet("Bolsa CAPES: R$ 2.100/mes (dedicacao exclusiva). Bolsa FAPESB: valores similares para programas na Bahia.")
pdf.bullet("Com Tecnologo em Analise de Sistemas + Economia, ele tem perfil para mestrado interdisciplinar (economia computacional, data science aplicada a politicas publicas).")

pdf.bold_body("Editais que estas acoes destravam em 2027:")
pdf.bullet("Voce: editais MGI (BI + Power Platform), editais IBGE (Python + QGIS + metodologia), editais AGU (LGPD)")
pdf.bullet("Irmao: editais de gestao publica e economia. Com o tecnologo, tambem editais de dados do IBGE e MGI.")

# --- FASE 2: 2027 ---
pdf.add_page()
pdf.title2("6.2 FASE 2: 2027 - Conseguir o primeiro edital pos-BRA 23/023")

pdf.title3("Para voce (orcamento: R$ 0-500/mes nesta fase):")
pdf.bullet("Concluir Pos Gestao Publica (i9) - ja em andamento, sem custo adicional.")
pdf.bullet("Mestrado Profissional em Ciencia da Computacao ou Ciencia de Dados (UFBA) - GRATUITO, inicio em marco 2027. O Mestrado stricto sensu reconhecido no Brasil e o maior multiplicador de pontuacao em editais PNUD. Com ele, voce passa a pontuar nos 58% dos editais que exigem/valorizam mestrado.")
pdf.bullet("OU: Mestrado em Engenharia Industrial (UFBA/PEI) se quiser manter o pe na engenharia.")
pdf.bullet("Certificacao Azure AZ-900 (Cloud Fundamentals) - gratuito (MS Learn) + R$ 210. Nuvem e cada vez mais pedida.")
pdf.bullet("Curso avancado Python para Ciencia de Dados (Coursera/Udemy) - R$ 30-50/mes.")
pdf.bullet("Manter 1 projeto PNUD ativo (edital conquistado em 2027) + portfolio atualizado.")

pdf.title3("Para o irmao (orcamento: R$ 0-500/mes nesta fase):")
pdf.bold_body("Se ja estiver empregado (Trilha A concretizada):")
pdf.bullet("Iniciar Especializacao em Economia do Setor Publico (UFBA) - gratuito, 12-18 meses, noturno.")
pdf.bullet("OU: Pos em Financas Publicas (FGV EAD) - ~R$ 400/mes, flexivel para quem trabalha.")
pdf.bullet("Certificacao Python para Analise de Dados (Coursera IBM) - R$ 150/mes, 3 meses.")
pdf.bullet("Candidatar-se a editais PNUD de economia e dados (TCU, IBGE).")

pdf.bold_body("Se estiver no Mestrado com bolsa (Trilha B concretizada):")
pdf.bullet("Dedicacao integral ao Mestrado em Economia (UFBA) com bolsa CAPES R$ 2.100/mes.")
pdf.bullet("Usar a dissertacao como case para editais futuros (ex: tema de tributacao, politicas publicas).")
pdf.bullet("Estagio docente ou pesquisa aplicada geram portfolio academico relevante.")
pdf.bullet("Primeira candidatura a edital PNUD no 2o semestre de 2027, ja com 1 ano de mestrado.")

pdf.bold_body("Editais que estas acoes destravam:")
pdf.bullet("Voce com mestrado UFBA + certificacoes Microsoft + experiencia PNUD: praticamente todos os editais de dados/TI/engenharia do PNUD")
pdf.bullet("Irmao: com emprego + pos, ou mestrado com bolsa, ja compete em editais de economia, tributacao, dados e gestao")

pdf.bold_body("Meta 2027: 1 edital conquistado (voce). Irmao com emprego ou no mestrado + primeira candidatura PNUD enviada.")

# --- FASE 3: 2028 ---
pdf.add_page()
pdf.title2("6.3 FASE 3: 2028 - Consolidacao e primeiro edital do irmao")

pdf.title3("Para voce (orcamento: R$ 200-600/mes):")
pdf.bullet("Continuar Mestrado UFBA (segundo ano). Usar o projeto de dissertacao como case para editais.")
pdf.bullet("Concluir Pos Industria 4.0. Tema quente para editais de governo digital e modernizacao.")
pdf.bullet("Certificacao Azure Data Engineer (DP-203) ou AWS Data Analytics - R$ 500 a prova. Abre editais maiores.")
pdf.bullet("Certificacao Scrum Master (PSM I) - R$ 600. Bem vista em editais de gestao de projetos.")
pdf.bullet("Manter 1-2 projetos PNUD simultaneos. Construir reputacao como consultor recorrente.")
pdf.bullet("Considerar abrir MEI para emissao de nota fiscal (necessario para alguns contratos).")

pdf.title3("Para o irmao (orcamento: R$ 0-500/mes):")
pdf.bold_body("Cenario A - Empregado + Pos concluida:")
pdf.bullet("Pos em Economia do Setor Publico ou Financas Publicas concluida. Curriculo com experiencia profissional + formacao + certificacoes.")
pdf.bullet("Certificacao Power BI PL-300 (MS Learn, R$ 300) - com o tecnologo em TI, ele tem base para tirar.")
pdf.bullet("Portfolio: projetos de analise de dados economicos no GitHub (ex: analise da carga tributaria, inflacao).")
pdf.bullet("Candidatar-se ativamente. Com emprego + pos + portfolio, ja e competitivo.")
pdf.bullet("Foco em editais: TCU (tributacao), IBGE (dados), PNUD direto (consultorias multidisciplinares).")

pdf.bold_body("Cenario B - Mestrado com bolsa (2o ano):")
pdf.bullet("Dissertacao em andamento. Possivel primeiro edital PNUD conquistado em 2027.")
pdf.bullet("O mestrado UFBA + experiencia PNUD = perfil imbatível para editais de economia.")
pdf.bullet("Ao concluir o mestrado, pode mirar editais de maior valor (TCU, BID, Banco Mundial).")

pdf.bold_body("Meta 2028: 2 editais simultaneos (1 voce + 1 irmao). Ambos com formacao completa e experiencia comprovada.")

# --- FASE 4: 2029 ---
pdf.title2("6.4 FASE 4: 2029 - Escala e diversificacao")

pdf.title3("Para voce:")
pdf.bullet("Mestrado UFBA concluido. Pos Industria 4.0 concluida. 5+ anos de experiencia em dados publicos (FIEB).")
pdf.bullet("3+ projetos PNUD no portfolio (2025, 2027, 2028). Carta de recomendacao de gestores PNUD.")
pdf.bullet("Considerar Doutorado? 50% dos editais pontuam. Mas so se fizer sentido estrategico (editais IBGE de alto valor).")
pdf.bullet("Abrir empresa (LTDA) junto com o irmao para pegar editais de pessoa juridica (valores maiores, projetos multidisciplinares).")
pdf.bullet("Ampliar para outras agencias ONU: UNESCO, ONU Mulheres, OIT tambem contratam no Brasil.")

pdf.title3("Para o irmao:")
pdf.bullet("Mestrado ou especializacao concluidos. Portfolio com pelo menos 1-2 projetos PNUD.")
pdf.bullet("Tecnologo em Analise de Sistemas + formacao em economia + experiencia PNUD = perfil senior.")
pdf.bullet("Candidatar-se a 3-4 editais por ano. Taxa de sucesso sobe com experiencia previa.")
pdf.bullet("Foco em: economia, tributacao, politicas publicas, dados, gestao.")
pdf.bullet("Pode atuar tambem em editais de TI/dados que tenham componente economica.")

pdf.bold_body("Meta 2029: 2 editais simultaneos consolidados. Iniciar operacao como PJ (voce + irmao) para projetos maiores e multidisciplinares.")

# ============================================
# 7. RESUMO: QUAL FORMACAO ABRE QUAL EDITAL
# ============================================
pdf.add_page()
pdf.title1("7. RESUMO: QUAL FORMACAO ABRE QUAL EDITAL")

pdf.body("Tabela de mapeamento direto entre formacoes e os tipos de edital que elas destravam:")

pdf.table(
    ["Formacao", "Tipo (custo/mes)", "Editais que Destrava", "Orgaos"],
    [
        ["PL-300 Power BI", "Certificacao (R$ 0-50)", "Editais de BI e dashboard", "MGI, futuros"],
        ["PL-900 Power Platform", "Certificacao (R$ 0-30)", "Editais de automacao M365", "MGI"],
        ["QGIS/ArcGIS basico", "Curso curto (gratis)", "Editais geoprocessamento", "IBGE"],
        ["Pos LGPD (i9)", "Pos-graduacao (ja paga)", "Editais protecao de dados", "AGU, IBGE"],
        ["Pos Gestao Publica (i9)", "Pos-graduacao (ja paga)", "Editais gestao/politicas publicas", "MGI, TCU, PNUD"],
        ["Pos Industria 4.0", "Pos-graduacao (ja paga)", "Editais governo digital", "MGI, PNUD"],
        ["Mestrado UFBA", "Stricto sensu (gratis)", "58% de TODOS os editais", "IBGE, TCU, MGI, AGU, PNUD"],
        ["Azure/AWS", "Certificacao (R$ 30-80)", "Editais cloud/dados avancados", "MGI, PNUD direto"],
        ["Scrum Master PSM I", "Certificacao (R$ 50)", "Editais com gestao de projetos", "MGI, PNUD"],
        ["Python Avancado", "Curso (R$ 30-50)", "Editais dados e automacao", "IBGE, MGI"],
    ],
    [36, 38, 62, 54]
)

pdf.ln(2)
pdf.title2("Para o irmao (Economista):")
pdf.table(
    ["Formacao", "Tipo (custo/mes)", "Editais que Destrava"],
    [
        ["Avaliacao Politicas Publicas", "Curso curto (gratis, ENAP)", "Editais de avaliacao e politicas publicas"],
        ["Orcamento Publico", "Curso curto (gratis, ILPF)", "Editais de financas publicas"],
        ["Google Data Analytics", "Certificacao (R$ 150/mes)", "Editais com analise quantitativa"],
        ["Pos Economia Setor Publico (UFBA)", "Pos-graduacao (gratis)", "Editais de economia e tributacao"],
        ["Mestrado Economia (UFBA)", "Stricto sensu (gratis)", "58% de TODOS + peso maximo em economia"],
        ["R/Python para Economistas", "Curso (R$ 30-50)", "Editais com dados economicos"],
    ],
    [62, 48, 80]
)

# ============================================
# 8. VISUALIZACAO TEMPORAL
# ============================================
pdf.add_page()
pdf.title1("8. CRONOGRAMA VISUAL 2026-2029")

pdf.body("Linha do tempo das formacoes, certificacoes e metas de editais:")

# Tabela de timeline
pdf.table(
    ["Periodo", "Voce - Formacoes", "Voce - Certificacoes", "Irmao - Formacoes", "Meta Editais"],
    [
        ["2026.2", "Concluir Quantic + LGPD(i9)", "PL-300, PL-900, QGIS basico", "ENAP, ILPF, Google Data", "Candidatar 3-5 editais"],
        ["2027.1", "Iniciar Mestrado UFBA", "Azure AZ-900", "Iniciar Pos/Mestrado UFBA", "Voce: 1 edital conquistado"],
        ["2027.2", "Concluir Gestao Publica(i9)", "Python avancado", "Continuar pos/mestrado", "Irmao: primeiras candidaturas"],
        ["2028.1", "Mestrado UFBA (2o ano)", "DP-203 ou AWS, PSM I", "Concluir pos/mestrado", "Ambos com editais ativos"],
        ["2028.2", "Concluir Industria 4.0", "Scrum, portfolio", "R/Python economia", "2 editais simultaneos"],
        ["2029", "Mestrado concluido. Doutorado?", "Avaliar certificacoes novas", "Consolidado no mercado", "PJ + 2+ editais/ano"],
    ],
    [26, 47, 47, 37, 33]
)

pdf.ln(3)
pdf.body(
    "Este cronograma e conservador e realista. Ele considera que voce ja tem uma base solida "
    "(graduacao dupla, experiencia FIEB, projeto PNUD em andamento) e que o gap principal e "
    "o mestrado stricto sensu brasileiro + certificacoes especificas de ferramentas. "
    "O irmao tem um caminho mais longo, mas com 2-3 anos de preparacao focada, torna-se competitivo."
)

# ============================================
# 9. CURSOS GRATUITOS COM CHANCELA
# ============================================
pdf.add_page()
pdf.title1("9. CURSOS GRATUITOS COM CHANCELA PARA PNUD")

pdf.body("Lista de formacoes gratuitas ou de baixo custo que sao bem vistas em processos seletivos da ONU:")

pdf.title2("9.1 Cursos de Orgaos Publicos Brasileiros")
pdf.bullet("ENAP - Escola Nacional de Administracao Publica: dezenas de cursos EAD gratuitos em gestao, politicas publicas, dados, inovacao. Certificado valido como horas complementares.")
pdf.bullet("TCU - Tribunal de Contas da Uniao: cursos de orcamento, auditoria, avaliacao de politicas publicas.")
pdf.bullet("ILPF - Instituto Legislativo: cursos de orcamento publico, processo legislativo.")
pdf.bullet("INPE - Instituto Nacional de Pesquisas Espaciais: geoprocessamento, QGIS, sensoriamento remoto (gratuitos, EAD).")
pdf.bullet("IBGE - Escola Nacional de Ciencias Estatisticas (ENCE): cursos e webinars gratuitos em estatistica.")

pdf.title2("9.2 Plataformas Internacionais (com opcao de bolsa)")
pdf.bullet("Coursera: Google Data Analytics, IBM Data Science, Python for Everybody. Pedir auxilio financeiro (financial aid) = gratuito.")
pdf.bullet("EdX: cursos de Harvard, MIT. Certificado pago, mas da para fazer gratis (sem certificado) ou pedir bolsa.")
pdf.bullet("Microsoft Learn: TODOS os modulos de Power BI, Azure, Power Platform, AI sao 100% gratuitos. So paga a prova de certificacao.")
pdf.bullet("AWS Skill Builder: mesmo modelo. Modulos gratuitos, prova da certificacao paga.")

pdf.title2("9.3 Pos-Graduacoes Publicas Gratuitas em Salvador")
pdf.bullet("UFBA - Mestrado em Ciencia da Computacao (PgCOMP): gratuito, conceito CAPES 5. Processo seletivo anual.")
pdf.bullet("UFBA - Mestrado em Economia: gratuito, conceito CAPES 5.")
pdf.bullet("UFBA - Mestrado Profissional em Engenharia Industrial (PEI): gratuito, combina engenharia + gestao.")
pdf.bullet("UFBA - Mestrado em Administracao: gratuito, conceito CAPES 5.")
pdf.bullet("UFBA - Especializacao em Politicas Publicas e Gestao Governamental.")

pdf.title2("9.4 Certificacoes Microsoft (custo apenas da prova)")
pdf.bullet("PL-300: Power BI Data Analyst - R$ 300. Validade: 1 ano (renovavel gratuitamente via MS Learn).")
pdf.bullet("PL-900: Power Platform Fundamentals - R$ 210.")
pdf.bullet("AZ-900: Azure Fundamentals - R$ 210.")
pdf.bullet("DP-900: Azure Data Fundamentals - R$ 210.")
pdf.bullet("PL-400: Power Platform Developer - R$ 420 (avancado, para depois do PL-900).")

# ============================================
# 10. RECOMENDACOES FINAIS
# ============================================
pdf.add_page()
pdf.title1("10. RECOMENDACOES FINAIS E PROXIMOS PASSOS")

pdf.title2("10.1 Esta Semana (ate 20/05)")
pdf.numbered(1, "Candidatar ao Edital 11/2026 (MGI, BI + Power Automate). Seu curriculo com Analise de Sistemas + experiencia em dados atende. Mesmo sem todas as certificacoes, vale tentar.")
pdf.numbered(2, "Candidatar ao TR 90/2026 (IBGE, Python + GIS).")
pdf.numbered(3, "Candidatar ao BRA20/023 (AGU, LGPD). Sua pos em LGPD e diretamente aplicavel.")
pdf.numbered(4, "Irmao: candidatar ao TR 07 e 08/2026 (TCU, tributacao).")

pdf.title2("10.2 Proximo Mes (Junho 2026)")
pdf.bullet("Fazer prova PL-300 (Power BI). Agendar no MS Learn.")
pdf.bullet("Criar perfil no UNGM (ungm.org).")
pdf.bullet("Atualizar curriculo formato ONU (P11).")
pdf.bullet("Irmao: concluir curso ENAP Avaliacao de Politicas Publicas.")

pdf.title2("10.3 Ate Dezembro 2026")
pdf.bullet("Concluir PL-900 + AZ-900.")
pdf.bullet("Curso QGIS basico (INPE).")
pdf.bullet("Montar GitHub com scripts e dashboards do projeto atual (anonimizados).")
pdf.bullet("Irmao: concluir Google Data Analytics Certificate.")
pdf.bullet("Ambos: monitorar novos editais semanalmente. O PNUD publica editais em ciclos de 2-4 semanas.")

pdf.title2("10.4 Vantagem Competitiva - Use o Projeto Atual")
pdf.body(
    "O projeto BRA 23/023 (edital 54/2025) que voce esta executando e seu maior ativo. "
    "Conhecer os processos internos do PNUD (validacao de produtos, prazos, relacao com gestores) "
    "coloca voce anos-luz a frente de candidatos que nunca trabalharam com a ONU. "
    "Ao final do projeto:\n"
    "- Solicite formalmente uma carta de recomendacao ao gestor PNUD/IBGE\n"
    "- Documente metricas de impacto (ex: 'sistema implementado reduziu em X% o tempo de processamento')\n"
    "- Peca para ser incluido no roster de consultores do PNUD (lista de pre-aprovados)\n"
    "- Use o projeto como case principal no curriculo, com resultados mensuraveis"
)

pdf.ln(4)
pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 4,
    "Nota: Este relatorio foi gerado a partir de dados publicos. TORs baixados e processados automaticamente. "
    "Valores e prazos conferidos em 17/05/2026. Recomenda-se a leitura completa de cada edital antes da candidatura. "
    "O Masters da Quantic nao e reconhecido como mestrado stricto sensu no Brasil, mas tem valor como especializacao internacional."
)

# ============================================
# 11. NETWORKING PARA PROJETOS DE CONSULTORIA
# ============================================
pdf.add_page()
pdf.title1("11. NETWORKING PARA PROJETOS DE CONSULTORIA")

pdf.body(
    "Conseguir projetos de consultoria - seja no PNUD ou em outros organismos - nao depende apenas "
    "de qualificacao tecnica. Networking estrategico e tao importante quanto o curriculo. "
    "Abaixo, um guia pratico para construir presenca e conexoes no ecossistema de consultoria ONU e alem."
)

pdf.title2("11.1 Dentro do PNUD (onde voce ja esta)")
pdf.bullet("Roster de consultores: ao final do projeto BRA 23/023, solicite formalmente ao gestor PNUD sua inclusao no roster de consultores pre-aprovados. Isso gera convites diretos para novos editais, sem necessidade de candidatura aberta.")
pdf.bullet("Carta de recomendacao: solicite ao gestor PNUD e ao contraparte do IBGE. Uma carta oficial da ONU tem peso enorme em qualquer processo seletivo futuro.")
pdf.bullet("Aprovadores: nomes como aline.santana, brenda.felix, livia.nogueira, rosana.tomazini, kalyandra.leite aparecem como aprovadores em dezenas de editais. Conecte-se com eles no LinkedIn APOS a entrega final do seu projeto. Nao durante - seria antiético.")
pdf.bullet("Eventos PNUD: o PNUD Brasil realiza webinars e workshops abertos. Participe e faca perguntas pertinentes no chat. Os palestrantes costumam anotar nomes.")

pdf.title2("11.2 Alem do PNUD: ecossistema ONU completo")
pdf.bullet("UNGM (ungm.org): Marketplace global de procurement da ONU. Cadastro gratuito. Configure alertas para 'Brazil' + 'Individual Consultant'. Todas as agencias ONU publicam la.")
pdf.bullet("Outras agencias ONU no Brasil que contratam PF:")
pdf.bullet("UNESCO - educacao, cultura, ciencia. Muitos editais de pesquisa e avaliacao.", indent=10)
pdf.bullet("ONU Mulheres - igualdade de genero, politicas publicas. Editais de analise de dados.", indent=10)
pdf.bullet("OIT (Organizacao Internacional do Trabalho) - empregabilidade, trabalho decente.", indent=10)
pdf.bullet("UNFPA (Fundo de Populacao) - demografia, saude publica, dados populacionais.", indent=10)
pdf.bullet("UNICEF - infancia, educacao, protecao social. Muitos editais de avaliacao.", indent=10)
pdf.bullet("FAO - agricultura, seguranca alimentar, meio ambiente.", indent=10)
pdf.bullet("OPAS/OMS - saude publica, epidemiologia, sistemas de saude.", indent=10)
pdf.bullet("UNOPS - infraestrutura, engenharia, TI. Editais maiores e mais tecnicos.", indent=10)
pdf.bullet("Cada agencia tem portal proprio de procurement. Cadastre-se em todas. Mesmo curriculo, multiplas vitrines.")

pdf.title2("11.3 LinkedIn Estrategico")
pdf.bullet("Perfil: titulo claro. Ex: 'Consultor PNUD | Engenheiro de Dados | Python & Power BI | Dados Publicos'. A primeira linha e a que aparece nas buscas.")
pdf.bullet("Postar sobre o projeto: com autorizacao do PNUD, publique insights anonimizados do projeto. Ex: 'Desafios de trabalhar com dados sensiveis no setor publico'. Isso atrai gestores de outros projetos.")
pdf.bullet("Hashtags: #PNUD #ConsultoriaONU #DadosPublicos #UNDP #DataForGood #GovernoDigital #PowerBI #Python")
pdf.bullet("Conectar com: aprovadores de editais, consultores que ja executaram projetos PNUD, gestores de organismos internacionais no Brasil.")
pdf.bullet("Grupos: buscar 'Consultores PNUD', 'ONU Brasil', 'UNDP Consultants' no LinkedIn. Entrar e interagir.")

pdf.title2("11.4 Grupos e Comunidades")
pdf.bullet("WhatsApp/Telegram: existem grupos informais de consultores ONU no Brasil. Pergunte a colegas do seu projeto atual. O boca-a-boca e a principal porta de entrada.")
pdf.bullet("Comunidade 'Consultores PNUD' no LinkedIn: grupos de discussao sobre editais, dicas de candidatura e oportunidades.")
pdf.bullet("Alumni UFBA: a UFBA tem ex-alunos em organismos internacionais. Use a rede de alumni para mentorias e indicacoes.")
pdf.bullet("Eventos e conferencias: Congresso Brasileiro de Ciencia de Dados, Python Brasil, eventos do IBGE. Excelentes para networking presencial.")
pdf.bullet("Devex.com: plataforma de carreira em desenvolvimento internacional. Plano basico pago (~US$ 10/mes), mas o trial gratuito ja da acesso a listas de oportunidades.")

pdf.title2("11.5 Networking para o Irmao")
pdf.bullet("LinkedIn: titulo 'Economista | Analise de Dados | Python & Power BI | Politicas Publicas'.")
pdf.bullet("Postar analises de conjuntura economica com graficos (Power BI/Streamlit) - mostra dominio tecnico + economico simultaneamente.")
pdf.bullet("Grupos de economistas: Conselho Regional de Economia (CORECON-BA), ANPEC (pos-graduacao em economia), FGV IBRE.")
pdf.bullet("Eventos: seminarios do BNDES, IPEA, Banco Central. Muitos sao online e gratuitos.")

# ============================================
# 12. ALEM DO PNUD: ONDE CONSEGUIR PROJETOS SIMILARES
# ============================================
pdf.add_page()
pdf.title1("12. ALEM DO PNUD: ONDE CONSEGUIR PROJETOS SIMILARES")

pdf.body(
    "O PNUD e a porta de entrada, mas esta longe de ser a unica fonte de consultorias bem remuneradas. "
    "Abaixo, um mapeamento completo de organismos, plataformas e estrategias para diversificar "
    "suas fontes de projetos a partir de 2028/2029."
)

pdf.title2("12.1 Bancos Multilaterais e Organismos Internacionais")
pdf.table(
    ["Organismo", "Tipo de Projeto", "Perfil Demandado", "Como Acessar"],
    [
        ["BID (Banco Interamericano)", "Desenvolvimento, infraestrutura", "Economistas, engenheiros", "iadb.org > procurement"],
        ["Banco Mundial", "Politicas publicas, avaliacao", "Economistas, estatisticos", "worldbank.org > procurement"],
        ["CAF (Corp. Andina de Fomento)", "Infraestrutura, desenvolvimento", "Engenheiros, economistas", "caf.com > licitacoes"],
        ["UNOPS", "Infraestrutura, TI, gestao", "Engenheiros, TI, arquitetos", "unops.org > procurement"],
        ["OPAS/OMS", "Saude publica, epidemiologia", "Medicos, estatisticos, TI", "paho.org > procurement"],
        ["FAO", "Agricultura, meio ambiente", "Agronomos, biologos, TI", "fao.org > procurement"],
    ],
    [36, 44, 44, 66]
)

pdf.title2("12.2 Orgaos e Fundacoes Nacionais")
pdf.table(
    ["Organismo", "Tipo de Projeto", "Perfil Demandado", "Como Acessar"],
    [
        ["IPEA", "Pesquisa economica e social", "Economistas, estatisticos", "Chamadas publicas, bolsas"],
        ["FGV Projetos", "Consultoria aplicada", "Multidisciplinar", "FGV contrata PF e PJ por projeto"],
        ["SEBRAE", "Consultoria empresarial, dados", "Gestao, TI, dados", "Editais estaduais SEBRAE"],
        ["BNDES", "Desenvolvimento, inovacao", "Economistas, engenheiros", "Fundos setoriais, editais"],
        ["Finep", "Inovacao tecnologica", "Engenheiros, TI", "Chamadas publicas, Finep Inovacred"],
        ["Fundacoes Estaduais (FAPESB, FAPESP)", "Pesquisa aplicada", "Pesquisadores, academicos", "Editais estaduais de fomento"],
    ],
    [36, 44, 44, 66]
)

pdf.title2("12.3 Consultorias para Governos via Organismos Internacionais")
pdf.body(
    "Muitos projetos de consultoria para governos estaduais e municipais sao intermediados por organismos "
    "internacionais (PNUD, UNESCO, BID). Seu perfil e particularmente valioso aqui porque voce ja conhece "
    "o modus operandi.\n\n"
    "Exemplos de projetos tipicos:\n"
    "- PNUD + Governo da Bahia: projetos de desenvolvimento regional, dados socioeconomicos\n"
    "- BID + Prefeituras: modernizacao administrativa, governo digital\n"
    "- Banco Mundial + Estados: avaliacao de politicas publicas, saude, educacao\n\n"
    "Como acessar: monitorar os portais de procurement desses organismos filtrando por 'Brazil'. "
    "Muitos projetos estaduais/municipais nao aparecem no portal PNUD Brasil, apenas no UNGM ou Quantum."
)

pdf.title2("12.4 Plataformas Agregadoras de Oportunidades")
pdf.bullet("UNGM (ungm.org): agrega editais de TODAS as agencias ONU. Cadastro unico. Gratuito. Configure alertas.")
pdf.bullet("Quantum (UNDP): sistema de procurement do PNUD. Acesso via parceiros.undp.org.br para Brasil.")
pdf.bullet("BID Procurement: editais do Banco Interamericano na America Latina. Muitos no Brasil.")
pdf.bullet("Devex (devex.com): plataforma de carreira em desenvolvimento internacional. Versao paga (~US$ 10-20/mes), mas e a mais completa. Tem filtro por pais, area e tipo de contrato.")
pdf.bullet("ReliefWeb (reliefweb.int): foco em ajuda humanitaria, mas tem editais de consultoria na area social.")

pdf.title2("12.5 Consultorias-Boutique e Mercado Privado")
pdf.body(
    "Para alem do setor publico e ONU, ha um mercado robusto de consultorias economicas e de dados "
    "que contratam profissionais com seu perfil:\n"
    "- Consultorias economicas: LCA Consultores, Tendencias, GO Associados, MB Associados, Rosenberg. Contratam economistas com stack de dados.\n"
    "- Consultorias de dados: Indicium, A3Data, DP6, Data H. Contratam engenheiros de dados e cientistas de dados.\n"
    "- Fintechs e bancos em Salvador/remoto: Nubank, Stone, PicPay, Banco Original. Programas de dados e analytics.\n"
    "- Para o irmao: alem das consultorias economicas, vagas de analista de dados economicos no mercado financeiro (XP, BTG, Itau, Bradesco). Todas tem areas de macroeconomia e dados."
)

pdf.title2("12.6 Estrategia de Diversificacao (2028-2029)")
pdf.body(
    "A partir de 2028, quando voce ja tiver mestrado UFBA + 2-3 projetos PNUD no portfolio:\n\n"
    "1. Manter PNUD como cliente recorrente (1-2 editais/ano) - ja conhece o sistema, a taxa de sucesso e alta.\n"
    "2. Expandir para BID e Banco Mundial - valores maiores (US$ 20-50k por contrato), projetos mais longos.\n"
    "3. Abrir empresa (LTDA) com o irmao - permite pegar editais PJ que pagam 2-3x mais que PF.\n"
    "4. Atuar como subcontratado de consultorias maiores (FGV, consultorias-boutique) - menos risco, fluxo constante.\n"
    "5. Criar presenca digital: blog/Substack sobre dados publicos, LinkedIn ativo, portfolio no GitHub. "
    "Isso gera inbound - gestores de projetos entram em contato com voce, em vez de voce correr atras de editais."
)

# Salvar PDF
pdf.output(str(OUTPUT_PDF))
print(f"PDF gerado: {OUTPUT_PDF} ({Path(OUTPUT_PDF).stat().st_size / 1024:.0f} KB)")

# ============================================
# EXCEL
# ============================================
print("Gerando Excel...")
df_editais = pd.DataFrame(editais)
df_editais["ferramentas"] = ""
df_editais["valor_total"] = ""
df_editais["mestrado"] = ""
df_editais["area_classificada"] = ""

for i, row in df_editais.iterrows():
    torid = str(row.get("torid", ""))
    # Valor total do contrato
    comentario = str(row.get("comments", "") or "")
    vt = extrair_valor_total(comentario, torid)
    df_editais.at[i, "valor_total"] = f"R$ {vt:,.2f}" if vt else ""
    
    for q in qualificacoes:
        if q.get("torid") == torid:
            df_editais.at[i, "ferramentas"] = ", ".join(q.get("ferramentas", []))
            df_editais.at[i, "mestrado"] = "Sim" if q.get("mestrado") else "Nao"
            grads = q.get("graduacao", [])
            if any(g in ["ciência da computação", "sistemas de informação", "tecnologia da informação", "ciência de dados"] for g in grads):
                df_editais.at[i, "area_classificada"] = "TI/Dados"
            elif "economia" in grads or "políticas públicas" in grads:
                df_editais.at[i, "area_classificada"] = "Economia/Gestao"
            elif "direito" in grads:
                df_editais.at[i, "area_classificada"] = "Juridico"
            elif "engenharia" in grads or "geografia" in grads or "biologia" in grads:
                df_editais.at[i, "area_classificada"] = "Engenharia/Ambiental"
            else:
                df_editais.at[i, "area_classificada"] = "Multidisciplinar"
            break

with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    df_editais.to_excel(writer, sheet_name="Editais_Completos", index=False)
    
    pd.DataFrame({
        "Ferramenta": [f for f, _ in ferramentas_counter.most_common(20)],
        "Qtd": [c for _, c in ferramentas_counter.most_common(20)],
    }).to_excel(writer, sheet_name="Ferramentas", index=False)
    
    pd.DataFrame({
        "Graduacao": [g for g, _ in graduacao_counter.most_common(20)],
        "Qtd": [c for _, c in graduacao_counter.most_common(20)],
    }).to_excel(writer, sheet_name="Graduacoes", index=False)
    
    if editais_dados:
        pd.DataFrame(editais_dados).to_excel(writer, sheet_name="Editais_Dados_TI", index=False)
    if editais_economista:
        pd.DataFrame(editais_economista).to_excel(writer, sheet_name="Para_Economista", index=False)

print(f"Excel gerado: {OUTPUT_EXCEL}")
print("Concluido!")
