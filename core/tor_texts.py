"""Persistência do texto extraído dos ToRs, comprimido e versionado no git.

Os PDFs e zips baixados ficam em `dados_brutos/tors/`, que é gitignored — o
runner do GitHub Actions é efêmero, então nada ali sobrevive de um dia para o
outro. O texto extraído, por outro lado, é pequeno (~4 KB por ToR em gzip) e
precisa continuar disponível depois que o ToR já foi processado: é dele que
`core/tor_values.py` extrai o valor total do contrato. Por isso ele mora numa
pasta própria, versionada.
"""
import gzip
import logging
import re

from core.config import TORS_DIR, TORS_TEXTO_DIR

logger = logging.getLogger(__name__)

MAX_CHARS = 50_000


def _slug(torid) -> str:
    """Nome de arquivo seguro para o torid.

    Cobre tanto os ids numéricos do PNUD quanto os prefixados de UNESCO/OEI
    ("unesco:123", "oei:algum-slug"), cujo ":" não pode ir para o disco.
    """
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(torid))


def salvar_texto(torid, texto: str) -> None:
    """Grava o texto do ToR comprimido, truncado em MAX_CHARS."""
    TORS_TEXTO_DIR.mkdir(parents=True, exist_ok=True)
    destino = TORS_TEXTO_DIR / f"{_slug(torid)}.txt.gz"
    # mtime=0 mantém a saída determinística: sem isso, reprocessar o mesmo ToR
    # produziria bytes diferentes e um diff espúrio a cada run diário.
    destino.write_bytes(gzip.compress(texto[:MAX_CHARS].encode(), compresslevel=9, mtime=0))


def ler_texto(torid) -> str | None:
    """Lê o texto do ToR, ou None se ele não tiver sido extraído ainda."""
    slug = _slug(torid)

    comprimido = TORS_TEXTO_DIR / f"{slug}.txt.gz"
    if comprimido.exists():
        try:
            return gzip.decompress(comprimido.read_bytes()).decode()
        except (OSError, EOFError, UnicodeDecodeError) as e:
            logger.warning("Falha ao ler texto comprimido do ToR %s: %s", torid, e)

    # Textos gravados antes da compressão, ainda presentes em checkouts locais.
    legado = TORS_DIR / f"{slug}_texto.txt"
    if legado.exists():
        return legado.read_text()

    return None
