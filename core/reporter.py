from datetime import datetime
from pathlib import Path

import pandas as pd
from fpdf import FPDF

from core.config import OUTPUT_EXCEL, OUTPUT_PDF


class _PDFReport(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(0, 51, 102)
            self.cell(0, 5, "Análise de Editais PNUD Brasil", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(0, 51, 102)
            self.line(self.l_margin, self.get_y() + 1, self.l_margin + self.w, self.get_y() + 1)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140)
        self.cell(0, 8, f"Página {self.page_no()}/{{nb}} | {datetime.now().strftime('%d/%m/%Y')}", align="C")

    def titulo(self, text: str):
        self.ln(2)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 51, 102)
        self.line(self.l_margin, self.get_y() + 1, self.l_margin + self.w, self.get_y() + 1)
        self.ln(4)

    def subtitulo(self, text: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 70, 130)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def corpo(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text: str, indent: int = 5):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        x0 = self.l_margin + indent
        self.set_x(x0)
        self.cell(3, 5, "-")
        self.set_x(x0 + 4)
        self.multi_cell(self.w - indent - 4, 5, text)
        self.ln(0.5)

    def tabela(self, headers: list, rows: list, col_widths: list | None = None):
        if col_widths is None:
            col_widths = [self.w / len(headers)] * len(headers)
        total_w = sum(col_widths)
        col_widths = [w * self.w / total_w for w in col_widths]

        self.set_font("Helvetica", "B", 7)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, fill=True)
        self.ln()

        self.set_font("Helvetica", "", 7)
        for r_idx, row in enumerate(rows):
            if r_idx % 2 == 0:
                self.set_fill_color(242, 246, 252)
            else:
                self.set_fill_color(255, 255, 255)
            self.set_text_color(60)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 5, str(cell)[:80], border=1, fill=True)
            self.ln()
        self.ln(3)


def gerar_excel(analise: dict) -> Path:
    editais = analise["editais"]
    if not editais:
        return OUTPUT_EXCEL

    df = pd.DataFrame(editais)
    colunas = ["id", "torid", "titulo", "tipo", "areas_tematicas", "perfil_classificado",
               "data_inicio", "data_fim", "local", "orgao_parceiro",
               "valor_estimado", "valor_estimado_num", "status"]
    colunas_existentes = [c for c in colunas if c in df.columns]
    df = df[colunas_existentes]

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Editais_Analisados", index=False)

        resumo = [{"Métrica": "Total de Editais", "Valor": analise["total_editais"]}]
        filtro = analise.get("filtro_aplicado", {})
        if filtro.get("periodo_meses"):
            resumo.append({"Métrica": "Período", "Valor": f"Últimos {filtro['periodo_meses']} meses"})
        if filtro.get("perfil"):
            resumo.append({"Métrica": "Perfil", "Valor": filtro["perfil"]})
        pd.DataFrame(resumo).to_excel(writer, sheet_name="Resumo", index=False)

        if analise.get("contagem_tipos"):
            pd.DataFrame([
                {"Tipo": k, "Quantidade": v} for k, v in analise["contagem_tipos"].items()
            ]).to_excel(writer, sheet_name="Por_Tipo", index=False)

        if analise.get("contagem_areas"):
            pd.DataFrame([
                {"Área": k, "Quantidade": v} for k, v in analise["contagem_areas"].items()
            ]).to_excel(writer, sheet_name="Por_Area", index=False)

        if analise.get("por_perfil"):
            rows = [{"Perfil": nome, "Quantidade": d["quantidade"], "Descrição": d["descricao"]}
                    for nome, d in analise["por_perfil"].items()]
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name="Por_Perfil", index=False)

    return OUTPUT_EXCEL


def gerar_pdf(analise: dict) -> Path:
    editais = analise["editais"]
    total = analise["total_editais"]
    filtro = analise.get("filtro_aplicado", {})

    pdf = _PDFReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    _pdf_capa(pdf, total, filtro)
    _pdf_visao_geral(pdf, analise)
    _pdf_perfis(pdf, analise)
    _pdf_valores(pdf, analise)
    _pdf_lista_editais(pdf, editais)

    pdf.output(str(OUTPUT_PDF))
    return OUTPUT_PDF


def _pdf_capa(pdf: _PDFReport, total: int, filtro: dict):
    pdf.add_page()
    pdf.ln(25)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 12, "EDITAIS PNUD BRASIL", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, "Análise de Editais e Classificação por Perfil", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_draw_color(0, 51, 102)
    pdf.line(pdf.l_margin + 25, pdf.get_y(), pdf.l_margin + pdf.w - 25, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80)
    filtro_desc = "Todos os editais" if filtro.get("todos") else f"Últimos {filtro.get('periodo_meses', 3)} meses"
    pdf.cell(0, 7, f"Período: {filtro_desc}", align="C", new_x="LMARGIN", new_y="NEXT")
    if filtro.get("perfil"):
        pdf.cell(0, 7, f"Perfil: {filtro['perfil']}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"{total} editais analisados | {datetime.now().strftime('%d/%m/%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Fonte: parceiros.undp.org.br/opportunities", align="C", new_x="LMARGIN", new_y="NEXT")


def _pdf_visao_geral(pdf: _PDFReport, analise: dict):
    pdf.add_page()
    pdf.titulo("1. VISÃO GERAL")
    pdf.corpo(f"Total de editais analisados: {analise['total_editais']}")

    if analise.get("contagem_tipos"):
        pdf.subtitulo("1.1 Por Tipo de Edital")
        rows = [[k, str(v)] for k, v in analise["contagem_tipos"].items()]
        pdf.tabela(["Tipo", "Quantidade"], rows, [120, 50])

    if analise.get("contagem_areas"):
        pdf.subtitulo("1.2 Áreas Temáticas")
        rows = [[k, str(v)] for k, v in analise["contagem_areas"].items()]
        pdf.tabela(["Área Temática", "Quantidade"], rows, [120, 50])

    if analise.get("contagem_orgaos"):
        pdf.subtitulo("1.3 Órgãos Parceiros")
        rows = [[k, str(v)] for k, v in analise["contagem_orgaos"].items()]
        pdf.tabela(["Órgão", "Quantidade"], rows, [120, 50])


def _pdf_perfis(pdf: _PDFReport, analise: dict):
    pdf.add_page()
    pdf.titulo("2. CLASSIFICAÇÃO POR PERFIL")
    pdf.corpo("Cada edital foi automaticamente classificado de acordo com o perfil mais compatível, "
              "baseado nas áreas temáticas, ferramentas exigidas, graduações e idiomas.")

    if analise.get("contagem_perfis"):
        rows = [[k, str(v)] for k, v in analise["contagem_perfis"].items() if k != "Não classificado"]
        if rows:
            pdf.tabela(["Perfil", "Quantidade"], rows, [120, 50])

    if analise.get("por_perfil"):
        pdf.subtitulo("2.1 Detalhamento por Perfil")
        for nome, dados in analise["por_perfil"].items():
            pdf.subtitulo(f"Perfil: {nome}")
            pdf.corpo(f"Descrição: {dados.get('descricao', 'N/D')}")
            pdf.corpo(f"Editais compatíveis: {dados['quantidade']}")
            for e in dados.get("editais", [])[:3]:
                score = e.get("score", 0)
                pdf.bullet(f"[ID {e['id']}] {e['titulo'][:120]} (score: {score:.0%})")


def _pdf_valores(pdf: _PDFReport, analise: dict):
    valores = analise.get("valores", {})
    if not valores or valores.get("quantidade_com_valor", 0) == 0:
        return
    pdf.add_page()
    pdf.titulo("3. VALORES ESTIMADOS")
    pdf.corpo(f"Editais com valor identificado: {valores['quantidade_com_valor']}")
    for label, key in [("Mínimo", "minimo"), ("Máximo", "maximo"), ("Médio", "medio"), ("Mediano", "mediano")]:
        v = valores.get(key)
        if v:
            pdf.corpo(f"{label}: R$ {v:,.2f}")


def _pdf_lista_editais(pdf: _PDFReport, editais: list):
    pdf.add_page()
    pdf.titulo("4. LISTA DE EDITAIS")
    for e in editais[:50]:
        titulo = e.get("titulo", "")[:100]
        pdf.bullet(f"[{e.get('id', '')}] {titulo}")
        pdf.bullet(f"Tipo: {e.get('tipo', '')} | Perfil: {e.get('perfil_classificado', '')} "
                   f"| Valor: R$ {e.get('valor_estimado') or 'NI'} "
                   f"| Órgão: {e.get('orgao_parceiro', '')}", indent=8)
        pdf.ln(1)


def gerar_relatorio_completo(analise: dict, novidades: dict | None = None) -> tuple[Path, Path]:
    from core.site_generator import gerar_dados_site

    excel_path = gerar_excel(analise)
    print(f"📊 Excel salvo em: {excel_path}")
    pdf_path = gerar_pdf(analise)
    print(f"📄 PDF salvo em: {pdf_path}")

    site_json, perfis_json = gerar_dados_site(analise, novidades)
    print(f"🌐 Dados do site salvos em: {site_json}")
    print(f"👤 Perfis do site salvos em: {perfis_json}")
    return excel_path, pdf_path
