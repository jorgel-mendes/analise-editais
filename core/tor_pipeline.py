"""Baixa e extrai o ToR de editais que ainda não têm qualificação processada.

Fluxo, por edital pendente: localizar a linha na tabela de oportunidades pelo
título, clicar no botão de download (baixa um .zip nomeado "{torid}.zip"),
descompactar, extrair texto do PDF e rodar a extração de qualificações por
regex — tudo no mesmo passo em que o arquivo é baixado.
"""
import asyncio
import json
import logging
import re
import zipfile
from pathlib import Path

from core.config import API_URL, DADOS_BRUTOS_DIR, TORS_DIR

logger = logging.getLogger(__name__)

QUALIFICACOES_FILE = DADOS_BRUTOS_DIR / "qualificacoes_extraidas.json"

GRAD_PATTERNS = [
    "ciência da computação", "engenharia de software", "sistemas de informação",
    "tecnologia da informação", "análise de sistemas", "engenharia da computação",
    "engenharia", "economia", "administração", "estatística", "geografia",
    "geologia", "biologia", "ecologia", "engenharia química", "engenharia ambiental",
    "direito", "ciências sociais", "sociologia", "antropologia", "história",
    "arquitetura", "urbanismo", "ciência de dados", "inteligência artificial",
    "matemática", "física", "química", "ciências contábeis", "gestão pública",
    "políticas públicas", "saúde pública", "medicina", "enfermagem", "comunicação",
    "biblioteconomia", "arquivologia", "ciência política", "relações internacionais",
]

FERRAMENTAS_LIST = [
    "power bi", "power automate", "power query", "dax", "power platform",
    "sharepoint", "microsoft 365", "outlook", "teams", "planner",
    "python", "r", "sql", "excel", "tableau", "qgis", "arcgis",
    "powerpoint", "word", "access", "sei", "sic", "dataverse",
    "google earth engine", "stata", "spss", "sas", "matlab",
    "git", "docker", "azure", "aws", "google cloud",
    "office 365", "project online",
]

CERT_PATTERNS = [
    "pmp", "scrum", "itil", "cobit", "cissp", "comptia",
    "microsoft certified", "aws certified", "google certified",
    "bsafe", "security clearance",
]


def _extract_pdf_text(pdf_path: Path) -> str:
    import pdfplumber

    try:
        with pdfplumber.open(pdf_path) as pdf:
            texts = [t for page in pdf.pages if (t := page.extract_text())]
            return "\n".join(texts)
    except Exception as e:
        logger.warning("Falha ao extrair texto de %s: %s", pdf_path, e)
        return ""


def _find_qualifications(text: str, torid: str) -> dict:
    """Extrai qualificações estruturadas do texto do ToR (regex, sem IA)."""
    result = {
        "torid": torid,
        "graduacao": [],
        "pos_graduacao": [],
        "mestrado": False,
        "doutorado": False,
        "anos_experiencia": None,
        "ferramentas": [],
        "idiomas": [],
        "certificacoes": [],
        "valor": None,
        "area_principal": "",
        "requisitos_obrigatorios": [],
        "requisitos_desejaveis": [],
    }

    text_lower = text.lower()

    for p in GRAD_PATTERNS:
        if p in text_lower:
            result["graduacao"].append(p)

    for term in ["pós-graduação", "especialização", "lato sensu", "mba"]:
        if term in text_lower:
            result["pos_graduacao"].append(term)

    if any(t in text_lower for t in ["mestrado", "mestre", "stricto sensu"]):
        result["mestrado"] = True
    if any(t in text_lower for t in ["doutorado", "doutor", "phd"]):
        result["doutorado"] = True

    exp_match = re.search(r'(\d+)\s*(?:\(.*?\))?\s*anos?\s*(?:de\s*)?experi[êe]ncia', text_lower)
    if exp_match:
        result["anos_experiencia"] = int(exp_match.group(1))

    for f in FERRAMENTAS_LIST:
        if f in text_lower:
            result["ferramentas"].append(f)

    if "inglês" in text_lower or "english" in text_lower:
        result["idiomas"].append("Inglês")
    if "espanhol" in text_lower or "spanish" in text_lower:
        result["idiomas"].append("Espanhol")

    for c in CERT_PATTERNS:
        if c in text_lower:
            result["certificacoes"].append(c)

    valor_match = re.search(r'R\$\s*([\d.]+,\d{2})', text)
    if not valor_match:
        valor_match = re.search(r'valor\s*(?:total\s*)?(?:da\s*contratação\s*)?:?\s*R\$\s*([\d.]+,\d{2})', text_lower)
    if valor_match:
        result["valor"] = valor_match.group(1)

    req_match = re.search(
        r'(?:requisitos?\s*obrigat[óo]rios?\s*:?|qualifica[cç][ãa]o\s*obrigat[óo]ria)(.*?)'
        r'(?:requisitos?\s*desej[áa]veis|crit[ée]rios\s*de\s*avalia[cç][ãa]o|processo\s*seletivo|'
        r'qualifica[cç][ãa]o\s*desej[áa]vel|\d+\.\s*entrega|\d+\.\s*cronograma)',
        text_lower, re.DOTALL,
    )
    if req_match:
        result["requisitos_obrigatorios"] = [
            l.strip() for l in req_match.group(1).split("\n") if l.strip() and len(l.strip()) > 20
        ][:10]

    req_desej_match = re.search(
        r'(?:requisitos?\s*desej[áa]veis|qualifica[cç][ãa]o\s*desej[áa]vel)(.*?)'
        r'(?:processo\s*seletivo|crit[ée]rios\s*de\s*pontua[cç][ãa]o|entrega\s*dos\s*produtos|'
        r'\d+\.\s*entrega|\d+\.\s*cronograma)',
        text_lower, re.DOTALL,
    )
    if req_desej_match:
        result["requisitos_desejaveis"] = [
            l.strip() for l in req_desej_match.group(1).split("\n") if l.strip() and len(l.strip()) > 20
        ][:10]

    return result


def _carregar_qualificacoes_existentes() -> dict[str, dict]:
    if not QUALIFICACOES_FILE.exists():
        return {}
    dados = json.loads(QUALIFICACOES_FILE.read_text())
    return {str(q.get("torid", "")): q for q in dados}


def _salvar_qualificacoes(qual_por_torid: dict[str, dict]):
    lista = list(qual_por_torid.values())
    QUALIFICACOES_FILE.write_text(json.dumps(lista, indent=2, ensure_ascii=False))


def _processar_zip_baixado(torid: str, zip_path: Path, edital: dict) -> dict | None:
    extract_dir = TORS_DIR / f"{torid}_extracted"
    extract_dir.mkdir(exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(extract_dir)
    except zipfile.BadZipFile:
        logger.warning("ToR %s: zip inválido", torid)
        return None

    pdfs = list(extract_dir.glob("*.pdf"))
    tor_pdf = next((f for f in pdfs if f.name == "TOR.pdf"), None) or (pdfs[0] if pdfs else None)
    if not tor_pdf:
        logger.warning("ToR %s: nenhum PDF encontrado no zip", torid)
        return None

    text = _extract_pdf_text(tor_pdf)
    if not text:
        return None

    (TORS_DIR / f"{torid}_texto.txt").write_text(text[:50000])

    qual = _find_qualifications(text, torid)
    qual["titulo"] = edital.get("title", "")
    qual["descricao"] = edital.get("description", "")
    qual["local"] = edital.get("local", "")
    qual["data_fim"] = (edital.get("endDate", "") or "")[:10]
    return qual


async def _baixar_e_extrair_async(pendentes: list[dict]) -> dict[str, dict]:
    from playwright.async_api import async_playwright

    restantes = {str(e["title"]).strip(): e for e in pendentes if e.get("title")}
    novas_qualificacoes: dict[str, dict] = {}
    if not restantes:
        return novas_qualificacoes

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
        )
        page = await context.new_page()

        try:
            await page.goto(API_URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            logger.warning("Falha ao carregar página de oportunidades: %s", e)
            await browser.close()
            return novas_qualificacoes

        await page.wait_for_timeout(3000)
        rows = await page.query_selector_all("mat-row")

        for row in rows:
            if not restantes:
                break
            try:
                text = (await row.inner_text()).strip()
            except Exception:
                continue

            titulo_match = next((t for t in restantes if t in text), None)
            if not titulo_match:
                continue
            edital = restantes.pop(titulo_match)
            torid = str(edital.get("torid", ""))
            if not torid:
                continue

            try:
                btn = await row.query_selector("mat-cell:last-child button")
                if not btn:
                    logger.info("ToR %s: sem botão de download na linha", torid)
                    continue

                async with page.expect_download(timeout=15000) as dl_info:
                    await btn.click()
                download = await dl_info.value

                zip_path = TORS_DIR / download.suggested_filename
                await download.save_as(str(zip_path))

                qual = _processar_zip_baixado(torid, zip_path, edital)
                if qual:
                    novas_qualificacoes[torid] = qual
                    logger.info("ToR %s extraído com sucesso", torid)
            except Exception as e:
                logger.warning("Falha ao baixar/processar ToR %s: %s", torid, e)

        await browser.close()

    return novas_qualificacoes


def baixar_e_extrair_tors(editais: list[dict]) -> int:
    """Baixa e extrai o ToR de cada edital ainda sem qualificação processada.

    Retorna quantos ToRs foram baixados e extraídos com sucesso nesta chamada.
    """
    TORS_DIR.mkdir(parents=True, exist_ok=True)
    existentes = _carregar_qualificacoes_existentes()

    pendentes = [
        e for e in editais
        if str(e.get("torid", "")) and str(e.get("torid", "")) not in existentes
    ]
    if not pendentes:
        return 0

    try:
        novas = asyncio.run(_baixar_e_extrair_async(pendentes))
    except Exception as e:
        logger.warning("Falha geral ao baixar/extrair ToRs: %s", e)
        return 0

    if novas:
        existentes.update(novas)
        _salvar_qualificacoes(existentes)

    return len(novas)
