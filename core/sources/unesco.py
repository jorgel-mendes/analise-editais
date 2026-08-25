"""Fonte UNESCO Brasil — plataforma Roster (apiroster.brasilia.unesco.org).

API JSON pública, sem autenticação. Só devolve o que está publicado agora
(sem histórico), então o snapshot diário é a única forma de acumular histórico.
"""
import logging

import requests

from core.config import UNESCO_API_URL, UNESCO_PORTAL_URL

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": "https://roster.brasilia.unesco.org",
}


def _listar_publicados() -> list[dict]:
    resp = requests.post(
        UNESCO_API_URL,
        data={"pageNumber": 1, "pageSize": 200},
        headers=_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def _pdf_url(file_id: str) -> str:
    return f"https://apiroster.brasilia.unesco.org/api/public/download/{file_id}"


def _normalizar(raw: dict) -> dict:
    eid = f"unesco:{raw['id']}"
    agencia = (raw.get("agency") or {}).get("name") or "UNESCO"
    anexos = raw.get("selectionProcessFile") or []

    return {
        "id": eid,
        "title": raw.get("title", ""),
        "description": raw.get("position", ""),
        "comments": "",
        "startDate": raw.get("startPublish", ""),
        "endDate": raw.get("endPublish") or raw.get("endDate", ""),
        "local": "",
        "receivingEmail": "",
        "statusDescription": (raw.get("selectionProcessStatus") or {}).get("description", ""),
        "created": raw.get("startPublish", ""),
        "torid": eid,
        "fonte": "unesco",
        "orgao_parceiro": agencia,
        "url_externo": UNESCO_PORTAL_URL,
        "tor_urls": [_pdf_url(a["fileId"]) for a in anexos if a.get("fileId")],
    }


def buscar_ativos() -> list[dict]:
    """Busca os processos seletivos atualmente publicados na Roster UNESCO Brasil."""
    try:
        publicados = _listar_publicados()
    except Exception as e:
        logger.warning("Falha ao buscar editais UNESCO: %s", e)
        return []
    return [_normalizar(e) for e in publicados]
