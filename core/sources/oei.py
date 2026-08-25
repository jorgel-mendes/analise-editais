"""Fonte OEI Brasil — site institucional (oei.int), sem API pública.

Estratégia: o WordPress expõe um sitemap XML completo e atualizado
(robots.txt libera tudo) com todas as licitações/contratações já publicadas,
inclusive histórico. A busca diária ("recentes") filtra pelo <lastmod> dos
últimos N dias; o backfill percorre o sitemap inteiro para popular o
histórico de uma vez (uso pontual, não faz parte do pipeline diário).
"""
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from core.config import OEI_SITEMAP_INDEX

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
_BRASIL_PATH = "/oficinas/brasil/contrataciones/"

_URL_BLOCK_RE = re.compile(r"<url>(.*?)</url>", re.S)
_SITEMAP_BLOCK_RE = re.compile(r"<sitemap>(.*?)</sitemap>", re.S)
_LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
_LASTMOD_RE = re.compile(r"<lastmod>([^<]+)</lastmod>")

_MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

# Radicais (PT/ES, m/f) de estados que indicam processo encerrado. Qualquer
# "Estado" que não contenha um destes é tratado como aberto — inclusive
# valores desconhecidos, para não descartar edital ativo por engano.
_ESTADOS_ENCERRADOS = (
    "adjudicad", "desert", "cancelad", "anulad", "resuelt", "resolvid",
    "finalizad", "cerrad", "encerrad", "declarad",
)


def _esta_ativo(estado: str) -> bool:
    e = (estado or "").strip().lower()
    return not any(termo in e for termo in _ESTADOS_ENCERRADOS)


def _parse_data_oei(texto: str) -> str:
    """Converte '23 Sep. 2025 · 00:00 (Hora BRA)' em '2025-09-23'."""
    m = re.match(r"(\d{1,2})\s+([A-Za-zçÇ]+)\.?\s+(\d{4})", texto.strip())
    if not m:
        return ""
    dia, mes_str, ano = m.groups()
    mes = _MESES.get(mes_str.lower().rstrip("."))
    if not mes:
        return ""
    return f"{ano}-{mes:02d}-{int(dia):02d}"


def _listar_sub_sitemaps() -> list[str]:
    resp = requests.get(OEI_SITEMAP_INDEX, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    urls = []
    for bloco in _SITEMAP_BLOCK_RE.findall(resp.text):
        m = _LOC_RE.search(bloco)
        if m and "contracting-sitemap" in m.group(1):
            urls.append(m.group(1).strip())
    return urls


def _listar_entradas_brasil(dias: int | None = None) -> list[dict]:
    corte = None
    if dias is not None:
        corte = (datetime.now(timezone.utc) - timedelta(days=dias)).date()

    entradas: dict[str, dict] = {}
    for sm_url in _listar_sub_sitemaps():
        try:
            resp = requests.get(sm_url, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Falha ao buscar sitemap OEI %s: %s", sm_url, e)
            continue

        for bloco in _URL_BLOCK_RE.findall(resp.text):
            loc_m = _LOC_RE.search(bloco)
            if not loc_m or _BRASIL_PATH not in loc_m.group(1):
                continue
            url = loc_m.group(1).strip()
            lastmod_m = _LASTMOD_RE.search(bloco)
            lastmod = lastmod_m.group(1).strip() if lastmod_m else ""

            if corte is not None:
                try:
                    data_lastmod = datetime.fromisoformat(lastmod).date()
                except ValueError:
                    data_lastmod = None
                if data_lastmod and data_lastmod < corte:
                    continue

            entradas[url] = {"url": url, "lastmod": lastmod}

    return list(entradas.values())


def _campo(campos: dict, chaves_possiveis: list[str]) -> str:
    for chave in chaves_possiveis:
        for k, v in campos.items():
            if chave.lower() in k.lower():
                return v
    return ""


def _parsear_detalhe(url: str, lastmod: str = "") -> dict | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Falha ao buscar edital OEI %s: %s", url, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.select_one("section.s__header h1")
    titulo = h1.get_text(strip=True) if h1 else ""
    if not titulo:
        return None

    cabecalho = {}
    for col in soup.select("section.s__header .__col"):
        label_el = col.select_one(".text-xs-regular")
        if not label_el:
            continue
        spans = col.find_all("span")
        cabecalho[label_el.get_text(strip=True)] = spans[-1].get_text(strip=True) if spans else ""

    campos = {}
    for item in soup.select(".__double_list_item"):
        titulo_el = item.select_one(".__title")
        texto_el = item.select_one(".__text")
        if titulo_el and texto_el:
            campos[titulo_el.get_text(strip=True)] = texto_el.get_text(" ", strip=True)

    localidade = _campo(campos, ["localidad"])
    fecha_fin = _campo(campos, ["fecha finalizaci", "fecha límite"])
    objeto = _campo(campos, ["objeto"])
    importe = _campo(campos, ["importe", "presupuesto"])
    email_txt = _campo(campos, ["correo"])

    pdfs = []
    for a in soup.select('a[href*=".pdf"]'):
        href = a.get("href")
        if href:
            pdfs.append(urljoin(url, href))

    data_publicada = ""
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else []
        for node in nodes:
            if isinstance(node, dict) and node.get("@type") == "WebPage" and node.get("datePublished"):
                data_publicada = node["datePublished"][:10]
                break
        if data_publicada:
            break

    inicio = data_publicada or (lastmod[:10] if lastmod else "")
    fim = _parse_data_oei(fecha_fin) or inicio

    m_orgao = re.search(r"OEI[/-]([A-Z0-9]{2,15})", titulo)
    orgao = f"OEI/{m_orgao.group(1)}" if m_orgao else "OEI"

    m_email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", email_txt)
    email_val = m_email.group(0) if m_email else ""

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    eid = f"oei:{slug}"

    return {
        "id": eid,
        "title": titulo,
        "description": objeto,
        "comments": importe,
        "startDate": inicio,
        "endDate": fim,
        "local": localidade,
        "receivingEmail": email_val,
        "statusDescription": cabecalho.get("Estado", ""),
        "created": inicio,
        "torid": eid,
        "fonte": "oei",
        "orgao_parceiro": orgao,
        "url_externo": url,
        "tor_urls": pdfs,
    }


def _buscar_detalhes(entradas: list[dict], max_workers: int = 6) -> list[dict]:
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futuros = {ex.submit(_parsear_detalhe, e["url"], e.get("lastmod", "")): e for e in entradas}
        for fut in as_completed(futuros):
            try:
                item = fut.result()
            except Exception as e:
                logger.warning("Falha ao processar edital OEI: %s", e)
                item = None
            if item:
                resultados.append(item)
    return resultados


def buscar_ativos(dias: int = 60) -> list[dict]:
    """Busca editais do Brasil publicados/atualizados nos últimos `dias` dias
    e filtra pelos que ainda estão em aberto (campo "Estado" da página)."""
    entradas = _listar_entradas_brasil(dias=dias)
    detalhes = _buscar_detalhes(entradas)
    return [d for d in detalhes if _esta_ativo(d.get("statusDescription", ""))]


def buscar_backfill(max_workers: int = 6) -> list[dict]:
    """Percorre o sitemap inteiro (todo o histórico do Brasil na OEI).

    Uso pontual/manual — não faz parte do pipeline diário (volume grande).
    """
    entradas = _listar_entradas_brasil(dias=None)
    logger.info("Backfill OEI: %d URLs encontradas no sitemap", len(entradas))
    return _buscar_detalhes(entradas, max_workers=max_workers)
