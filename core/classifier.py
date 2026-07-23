import re

from core.config import CLASSIFICACAO_TIPOS, AREAS_TEMATICAS, DOMINIO_ORGAO


def classificar_tipo(titulo: str, descricao: str = "") -> str:
    texto = f"{titulo} {descricao or ''}".lower()
    for tipo, palavras in CLASSIFICACAO_TIPOS.items():
        for p in palavras:
            if p in texto:
                return tipo
    return "Consultoria (tipo não especificado)"


def classificar_areas(titulo: str, descricao: str = "") -> list[str]:
    texto = f"{titulo} {descricao or ''}".lower()
    areas = []
    for area, palavras in AREAS_TEMATICAS.items():
        for p in palavras:
            if p in texto:
                areas.append(area)
                break
    return areas if areas else ["Não classificada"]


def extrair_orgao(email: str = "") -> str:
    if not email:
        return "Não identificado"
    dominio = email.split("@")[-1] if "@" in email else ""
    for dom, orgao in DOMINIO_ORGAO.items():
        if dom in dominio:
            return orgao
    return "Não identificado"


def extrair_valor(comentario: str = "") -> tuple[str | None, float | None]:
    if not comentario:
        return None, None
    match = re.search(r'R\$\s*([\d.]+,\d{2})', comentario)
    if match:
        texto = match.group(1)
        try:
            numero = float(texto.replace(".", "").replace(",", "."))
            return texto, numero
        except ValueError:
            return texto, None
    return None, None


def classificar_edital(edital: dict) -> dict:
    titulo = edital.get("title", "")
    descricao = edital.get("description", "") or ""
    comentario = edital.get("comments", "") or ""

    valor_texto, valor_num = extrair_valor(comentario)

    return {
        "id": edital["id"],
        "torid": edital.get("torid", ""),
        "titulo": titulo,
        "descricao": descricao,
        "tipo": classificar_tipo(titulo, descricao),
        "areas_tematicas": classificar_areas(titulo, descricao),
        "data_inicio": edital.get("startDate", "")[:10] if edital.get("startDate") else "",
        "data_fim": edital.get("endDate", "")[:10] if edital.get("endDate") else "",
        "local": edital.get("local", ""),
        "orgao_parceiro": extrair_orgao(edital.get("receivingEmail", "")),
        "email_submissao": edital.get("receivingEmail", ""),
        "valor_estimado": valor_texto,
        "valor_estimado_num": valor_num,
        "status": edital.get("statusDescription", ""),
        "data_criacao": edital.get("created", "")[:10] if edital.get("created") else "",
    }
