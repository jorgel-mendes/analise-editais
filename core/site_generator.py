import json
import logging
from datetime import datetime
from pathlib import Path

from core.config import ROOT
from core.bridge import carregar_qualificacoes, enriquecer_edital, calcular_match_detalhado
from core.perfil import carregar_perfis
from core.recommender import gerar_recomendacoes_todos_perfis
from core.classifier import classificar_edital

logger = logging.getLogger(__name__)

SITE_DATA_DIR = ROOT / "docs" / "data"
SITE_ANALISE_FILE = SITE_DATA_DIR / "analise.json"
SITE_PERFIS_FILE = SITE_DATA_DIR / "perfis.json"


def gerar_dados_site(analise: dict, novidades: dict | None = None) -> tuple[Path, Path]:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    site_data = _tentar_ia(analise) or _analise_deterministica(analise)

    if site_data:
        _mesclar_valores_tors(site_data["editais"])
        _recalcular_valores(site_data)
        site_data["gerado_em"] = datetime.now().isoformat()
        site_data["resumo"]["novos_hoje"] = novidades["novos_count"] if novidades else 0
        site_data["resumo"]["encerrados_hoje"] = novidades["encerrados_count"] if novidades else 0
        site_data["resumo_ia"] = _gerar_resumo(site_data)

    SITE_ANALISE_FILE.write_text(json.dumps(site_data, indent=2, ensure_ascii=False))

    perfis = carregar_perfis()
    SITE_PERFIS_FILE.write_text(json.dumps({"perfis": list(perfis.values())}, indent=2, ensure_ascii=False))

    return SITE_ANALISE_FILE, SITE_PERFIS_FILE


def _tentar_ia(analise: dict) -> dict | None:
    from core.persistence import carregar_editais_historico
    from core.llm import analisar_com_ia

    raw = carregar_editais_historico(meses=12)
    if not raw:
        return None

    logger.info("Tentando análise via DeepSeek...")
    resultado = analisar_com_ia(raw)
    if resultado:
        logger.info("Análise IA concluída com sucesso")
        return resultado
    return None


def _analise_deterministica(analise: dict) -> dict:
    qualificacoes = carregar_qualificacoes()
    perfis = carregar_perfis()

    editais_enriquecidos = []
    for edital in analise["editais"]:
        e = enriquecer_edital(edital, qualificacoes)
        matches = {}
        for nome_perfil, perfil in perfis.items():
            matches[nome_perfil] = calcular_match_detalhado(e, perfil)
        e["matches"] = matches
        e["url_externo"] = "https://parceiros.undp.org.br/opportunities"
        editais_enriquecidos.append(e)

    perfil_list = []
    for nome, perfil in perfis.items():
        count = sum(1 for e in editais_enriquecidos if e["matches"].get(nome, {}).get("score", 0) >= 0.15)
        perfil_list.append({
            "nome": nome,
            "descricao": perfil.get("descricao", ""),
            "graduacoes": perfil.get("graduacoes", []),
            "ferramentas": perfil.get("ferramentas", []),
            "areas_interesse": perfil.get("areas_interesse", []),
            "idiomas": perfil.get("idiomas", []),
            "match_count": count,
        })

    historicos = _carregar_historicos_enriquecidos(qualificacoes, perfis)

    return {
        "gerado_em": None,
        "resumo": {
            "total_editais": analise["total_editais"],
            "novos_hoje": 0,
            "encerrados_hoje": 0,
            "por_tipo": analise.get("contagem_tipos", {}),
            "por_area": analise.get("contagem_areas", {}),
            "por_orgao": analise.get("contagem_orgaos", {}),
            "valores": analise.get("valores", {}),
        },
        "perfis": perfil_list,
        "editais": editais_enriquecidos,
        "recomendacoes": gerar_recomendacoes_todos_perfis(historicos),
        "modo": "deterministico",
    }


def _carregar_historicos_enriquecidos(qualificacoes: dict, perfis: dict) -> list:
    from core.persistence import carregar_editais_historico

    raw = carregar_editais_historico(meses=12)
    if not raw:
        return []

    classificados = [classificar_edital(e) for e in raw]
    enriquecidos = []
    for edital in classificados:
        e = enriquecer_edital(edital, qualificacoes)
        matches = {}
        for nome_perfil, perfil in perfis.items():
            matches[nome_perfil] = calcular_match_detalhado(e, perfil)
        e["matches"] = matches
        enriquecidos.append(e)

    return enriquecidos


def _recalcular_valores(site_data: dict):
    from statistics import median
    valores = [e["valor_estimado_num"] for e in site_data["editais"] if e.get("valor_estimado_num")]
    if valores:
        site_data["resumo"]["valores"] = {
            "minimo": min(valores),
            "maximo": max(valores),
            "medio": round(sum(valores) / len(valores), 2),
            "mediano": round(median(valores), 2),
            "quantidade_com_valor": len(valores),
        }


def _mesclar_valores_tors(editais: list):
    from core.tor_values import extrair_valores_tors
    from core.bridge import carregar_qualificacoes

    qual = carregar_qualificacoes()
    valores_tor = extrair_valores_tors(qual)

    for e in editais:
        torid = str(e.get("torid", ""))
        if torid in valores_tor:
            v = valores_tor[torid]
            if not e.get("valor_estimado_num") or v > e["valor_estimado_num"]:
                e["valor_estimado_num"] = v
                e["valor_estimado"] = f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            e["requisitos"]["valor_tor"] = v


def _gerar_resumo(site_data: dict) -> str | None:
    import os
    if not os.environ.get("DEEPSEEK_API_KEY"):
        return None

    try:
        from openai import OpenAI

        stats = json.dumps({
            "total": site_data["resumo"]["total_editais"],
            "por_tipo": site_data["resumo"].get("por_tipo", {}),
            "por_orgao": site_data["resumo"].get("por_orgao", {}),
            "por_area": dict(list(site_data["resumo"].get("por_area", {}).items())[:5]),
            "perfis": [{"nome": p["nome"], "match": p["match_count"]} for p in site_data.get("perfis", [])],
        }, ensure_ascii=False)

        client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Você é um analista. Escreva um resumo de 3-4 frases em português sobre os editais do PNUD Brasil. Destaque: total, áreas mais quentes, órgãos principais, e perfis mais demandados. Seja direto e informativo."},
                {"role": "user", "content": f"Resuma estes dados:\n{stats}"},
            ],
            temperature=0.3,
            max_tokens=300,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Falha ao gerar resumo IA: %s", e)
        return None

