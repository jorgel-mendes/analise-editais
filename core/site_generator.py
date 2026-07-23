import json
from datetime import datetime
from pathlib import Path

from core.config import PERFIS_DIR, ROOT
from core.bridge import carregar_qualificacoes, enriquecer_edital, calcular_match_detalhado
from core.perfil import carregar_perfis
from core.recommender import gerar_recomendacoes_todos_perfis
from core.classifier import classificar_edital

SITE_DATA_DIR = ROOT / "docs" / "data"
SITE_ANALISE_FILE = SITE_DATA_DIR / "analise.json"
SITE_PERFIS_FILE = SITE_DATA_DIR / "perfis.json"


def gerar_dados_site(analise: dict, novidades: dict | None = None) -> tuple[Path, Path]:
    """Gera os arquivos JSON consumidos pelo frontend."""
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

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

    editais_historicos = _carregar_historicos_enriquecidos(qualificacoes, perfis)

    site_data = {
        "gerado_em": datetime.now().isoformat(),
        "resumo": {
            "total_editais": analise["total_editais"],
            "novos_hoje": novidades["novos_count"] if novidades else 0,
            "encerrados_hoje": novidades["encerrados_count"] if novidades else 0,
            "por_tipo": analise.get("contagem_tipos", {}),
            "por_area": analise.get("contagem_areas", {}),
            "por_orgao": analise.get("contagem_orgaos", {}),
            "valores": analise.get("valores", {}),
        },
        "perfis": perfil_list,
        "editais": editais_enriquecidos,
        "recomendacoes": gerar_recomendacoes_todos_perfis(editais_historicos),
    }

    SITE_ANALISE_FILE.write_text(json.dumps(site_data, indent=2, ensure_ascii=False))

    perfis_data = {"perfis": list(perfis.values())}
    SITE_PERFIS_FILE.write_text(json.dumps(perfis_data, indent=2, ensure_ascii=False))

    return SITE_ANALISE_FILE, SITE_PERFIS_FILE


def _carregar_historicos_enriquecidos(qualificacoes: dict, perfis: dict) -> list:
    """Carrega editais dos últimos 12 meses, classifica e enriquece com qualificações."""
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
