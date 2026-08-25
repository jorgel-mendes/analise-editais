"""Baixa e extrai qualificações de ToRs com PDF de acesso direto (UNESCO, OEI).

Ao contrário do PNUD (tor_pipeline.py), essas fontes já expõem a URL do PDF
sem precisar de Playwright/download por clique — um GET simples resolve.
Reaproveita a extração por regex (_find_qualifications) do tor_pipeline.
"""
import logging

import requests

from core.config import TORS_DIR
from core.tor_pipeline import (
    _carregar_qualificacoes_existentes,
    _extract_pdf_text,
    _find_qualifications,
    _salvar_qualificacoes,
)

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def _baixar_e_extrair_um(edital: dict) -> dict | None:
    torid = str(edital["torid"])
    textos = []

    for i, url in enumerate(edital.get("tor_urls", [])):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Falha ao baixar PDF %s (%s): %s", url, torid, e)
            continue

        pdf_path = TORS_DIR / f"{torid.replace(':', '_')}_{i}.pdf"
        pdf_path.write_bytes(resp.content)
        texto = _extract_pdf_text(pdf_path)
        if texto:
            textos.append(texto)

    texto_total = "\n".join(textos)
    if not texto_total:
        return None

    (TORS_DIR / f"{torid.replace(':', '_')}_texto.txt").write_text(texto_total[:50000])

    qual = _find_qualifications(texto_total, torid)
    qual["titulo"] = edital.get("titulo") or edital.get("title", "")
    qual["descricao"] = edital.get("descricao") or edital.get("description", "")
    qual["local"] = edital.get("local", "")
    qual["data_fim"] = (edital.get("data_fim") or edital.get("endDate") or "")[:10]
    return qual


def baixar_e_extrair_tors_diretos(editais: list[dict]) -> int:
    """Baixa e extrai o(s) ToR(s) de cada edital com PDF direto e sem qualificação processada.

    Retorna quantos ToRs foram extraídos com sucesso nesta chamada.
    """
    TORS_DIR.mkdir(parents=True, exist_ok=True)
    existentes = _carregar_qualificacoes_existentes()

    pendentes = [
        e for e in editais
        if e.get("torid") and str(e["torid"]) not in existentes and e.get("tor_urls")
    ]
    if not pendentes:
        return 0

    novas: dict[str, dict] = {}
    for edital in pendentes:
        torid = str(edital["torid"])
        try:
            qual = _baixar_e_extrair_um(edital)
        except Exception as e:
            logger.warning("Falha geral ao processar ToR %s: %s", torid, e)
            continue
        if qual:
            novas[torid] = qual
            logger.info("ToR %s (%s) extraído com sucesso", torid, edital.get("fonte", ""))

    if novas:
        existentes.update(novas)
        _salvar_qualificacoes(existentes)

    return len(novas)
