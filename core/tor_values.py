import re
import logging
from pathlib import Path

from core.config import TORS_DIR

logger = logging.getLogger(__name__)


def extrair_valores_tors(qualificacoes: dict[str, dict]) -> dict[str, float]:
    """Extrai o valor TOTAL de cada ToR a partir do texto extraído do PDF.
    Retorna dicionário torid → valor_total (float)."""
    valores = {}

    for torid, qual in qualificacoes.items():
        valor = _extrair_valor_texto(torid)
        if valor:
            valores[torid] = valor
            continue

        valor = _extrair_valor_com_ia(torid)
        if valor:
            valores[torid] = valor

    logger.info("Valores ToR extraídos: %d/%d", len(valores), len(qualificacoes))
    return valores


def _extrair_valor_texto(torid: str) -> float | None:
    tor_text = TORS_DIR / f"{torid}_texto.txt"
    if not tor_text.exists():
        return None

    text = tor_text.read_text()
    patterns = [
        r'Valor\s+total\s+(?:da\s+contrata[cç][aã]o|do\s+contrato|do\s+perfil)\s*:?\s*R\$\s*([\d.]+,\d{2})',
        r'Total\s+do\s+perfil\s+.*?R\$\s*([\d.]+,\d{2})',
        r'valor\s+total\s+de\s+R\$\s*([\d.]+,\d{2})',
        r'(?:montante|valor)\s+total\s+.*?R\$\s*([\d.]+,\d{2})',
        r'Valor\s+da\s+contrata[cç][aã]o\s*:?\s*R\$\s*([\d.]+,\d{2})',
    ]

    candidates = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            try:
                v = float(m.replace(".", "").replace(",", "."))
                if v > 1000:
                    candidates.append(v)
            except ValueError:
                pass

    if candidates:
        return max(candidates)

    all_values = re.findall(r'R\$\s*([\d.]+,\d{2})', text)
    big_values = []
    for m in all_values:
        try:
            v = float(m.replace(".", "").replace(",", "."))
            if v > 20000:
                big_values.append(v)
        except ValueError:
            pass

    if big_values:
        candidates_sorted = sorted(big_values)
        if len(candidates_sorted) >= 2 and candidates_sorted[-1] > candidates_sorted[-2] * 5:
            return candidates_sorted[-1]
        return max(candidates_sorted)

    return None


def _extrair_valor_com_ia(torid: str) -> float | None:
    import os
    if not os.environ.get("DEEPSEEK_API_KEY"):
        return None

    tor_text = TORS_DIR / f"{torid}_texto.txt"
    if not tor_text.exists():
        return None

    text = tor_text.read_text()[:3000]
    if len(text) < 100:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Extraia o valor TOTAL do contrato do texto abaixo. Retorne APENAS o número (ex: 170000.00). Se não encontrar, retorne 'null'."},
                {"role": "user", "content": text},
            ],
            temperature=0,
            max_tokens=50,
        )

        result = response.choices[0].message.content.strip().lower()
        result = result.replace("r$", "").replace(".", "").replace(",", ".").strip()
        try:
            v = float(result)
            if v > 1000:
                return v
        except ValueError:
            pass
    except Exception as e:
        logger.warning("IA falhou ao extrair valor do ToR %s: %s", torid, e)

    return None
