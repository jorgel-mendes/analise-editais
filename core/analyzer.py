from collections import Counter
from datetime import datetime, timedelta

from core.classifier import classificar_edital
from core.perfil import classificar_perfil_do_edital, filtrar_por_perfil, carregar_perfis


def analisar_editais(
    editais: list,
    periodo_meses: int | None = 3,
    perfil_nome: str | None = None,
    todos: bool = False,
) -> dict:
    """Analisa editais com opções de período e perfil.

    Args:
        editais: Lista de editais brutos (do scraping)
        periodo_meses: Filtrar pelos últimos N meses (None = sem filtro)
        perfil_nome: Filtrar por perfil específico
        todos: Ignorar filtro de período (analisar todos)

    Returns:
        Dicionário com análises e metadados
    """
    classificados = [classificar_edital(e) for e in editais]

    if periodo_meses and not todos:
        corte = datetime.now() - timedelta(days=periodo_meses * 30)
        classificados = [
            e for e in classificados
            if e.get("data_inicio") and e["data_inicio"] >= corte.strftime("%Y-%m-%d")
        ]

    perfis_disponiveis = carregar_perfis()
    for edital in classificados:
        edital["perfil_classificado"] = classificar_perfil_do_edital(edital)

    if perfil_nome:
        classificados = filtrar_por_perfil(classificados, perfil_nome)

    return _gerar_estatisticas(classificados, perfis_disponiveis, periodo_meses, perfil_nome, todos)


def _gerar_estatisticas(
    classificados: list,
    perfis_disponiveis: dict,
    periodo_meses: int | None,
    perfil_nome: str | None,
    todos: bool,
) -> dict:
    total = len(classificados)

    contagem_tipos = Counter(e["tipo"] for e in classificados)

    areas_flat = []
    for e in classificados:
        areas = e.get("areas_tematicas", [])
        if isinstance(areas, list):
            areas_flat.extend(areas)
        elif isinstance(areas, str):
            areas_flat.extend(areas.split(", "))
    contagem_areas = Counter(areas_flat)

    contagem_orgaos = Counter(e["orgao_parceiro"] for e in classificados)

    contagem_perfis = Counter(e.get("perfil_classificado", "") for e in classificados)

    valores = []
    for e in classificados:
        v = e.get("valor_estimado_num")
        if v and v > 0:
            valores.append(v)

    # Distribuição por perfil
    por_perfil = {}
    for nome_perfil in perfis_disponiveis:
        matched = filtrar_por_perfil(classificados, nome_perfil)
        if matched:
            por_perfil[nome_perfil] = {
                "quantidade": len(matched),
                "descricao": perfis_disponiveis[nome_perfil].get("descricao", ""),
                "editais": [{"id": e["id"], "titulo": e["titulo"], "score": e.get("score_perfil", 0)} for e in matched[:5]],
            }

    return {
        "total_editais": total,
        "filtro_aplicado": {
            "periodo_meses": periodo_meses if not todos else None,
            "perfil": perfil_nome,
            "todos": todos,
        },
        "contagem_tipos": dict(contagem_tipos.most_common()),
        "contagem_areas": dict(contagem_areas.most_common(10)),
        "contagem_orgaos": dict(contagem_orgaos.most_common()),
        "contagem_perfis": dict(contagem_perfis.most_common()),
        "valores": {
            "minimo": min(valores) if valores else None,
            "maximo": max(valores) if valores else None,
            "medio": sum(valores) / len(valores) if valores else None,
            "mediano": sorted(valores)[len(valores) // 2] if valores else None,
            "quantidade_com_valor": len(valores),
        },
        "por_perfil": por_perfil,
        "editais": classificados,
        "data_analise": datetime.now().isoformat(),
    }
