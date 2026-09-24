from core.config import API_URL, OEI_PORTAL_URL, UNESCO_PORTAL_URL

_PORTAIS = {"pnud": API_URL, "unesco": UNESCO_PORTAL_URL, "oei": OEI_PORTAL_URL}


def fonte_do_edital(edital: dict) -> str:
    """Fonte do edital; cai no prefixo do id ("unesco:", "oei:") para registros antigos sem o campo."""
    fonte = edital.get("fonte")
    if fonte:
        return fonte
    prefixo = str(edital.get("id", "")).split(":", 1)[0]
    return prefixo if prefixo in _PORTAIS else "pnud"


def url_portal(edital: dict) -> str:
    """Link mais específico disponível para o edital no portal da fonte.

    Só a OEI tem página própria por edital; PNUD e UNESCO são SPAs sem rota
    pública por edital, então o link é a listagem pública do portal.
    """
    fonte = fonte_do_edital(edital)
    url = edital.get("url_externo") or ""
    if fonte == "oei" and url.startswith("https://oei.int/oficinas/"):
        return url
    return _PORTAIS[fonte]


def url_pdf(edital: dict) -> str:
    """PDF do edital quando o portal não tem página própria (UNESCO)."""
    if fonte_do_edital(edital) == "unesco":
        return (edital.get("tor_urls") or [""])[0] or edital.get("url_pdf", "")
    return ""


def aplicar_links(destino: dict, origem: dict):
    """Preenche fonte, url_externo e url_pdf de `destino` a partir do edital bruto `origem`."""
    destino["fonte"] = fonte_do_edital(origem)
    destino["url_externo"] = url_portal(origem)
    destino["url_pdf"] = url_pdf(origem)
