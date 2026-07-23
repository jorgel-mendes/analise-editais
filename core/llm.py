import json
import logging
import os
from collections import Counter

logger = logging.getLogger(__name__)

DEEPSEEK_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

CLASSIFY_PROMPT = """Classifique cada edital do PNUD Brasil. Retorne APENAS um array JSON com esta estrutura exata:

[{
  "id": 1,
  "tipo": "Consultoria Pessoa Física (PF)",
  "areas_tematicas": ["Saúde"],
  "orgao_parceiro": "TCU",
  "perfil_classificado": "pesquisador_computacao",
  "valor_estimado_num": 50000.0,
  "requisitos": {"graduacao": ["medicina"], "ferramentas": ["r"], "idiomas": ["inglês"], "anos_experiencia": 5, "mestrado": true, "doutorado": false},
  "matches": {
    "engenheiro_dados": {"score": 0.2, "areas": false, "ferramentas_match": [], "ferramentas_faltando": [], "graduacao_match": [], "graduacao_faltando": ["medicina"], "idiomas_match": ["inglês"], "idiomas_faltando": [], "comentario": "Área de saúde, sem afinidade"},
    "economista": {"score": 0.15, ...},
    "pesquisador_computacao": {"score": 0.3, ...}
  }
}]

MATCH — SEJA CONSERVADOR:
- Score 0.0-0.3: pouca compatibilidade
- Score 0.3-0.5: alguma interseção mas gaps significativos
- Score 0.5-0.7: boa compatibilidade — RARO
- Score 0.7-1.0: excepcional — MUITO RARO

PENALIZE:
- Exige mestrado e perfil tem tem_mestrado:false → score máx 0.4
- Exige doutorado e perfil tem tem_doutorado:false → score máx 0.3
- Experiência exigida > experiencia_anos do perfil → reduza
- Graduação exigida não está no perfil → reduza 0.2-0.3
- Áreas temáticas incompatíveis → score máx 0.2

CALCULE matches PARA CADA PERFIL (engenheiro_dados, economista, pesquisador_computacao) presente no JSON de entrada.

Retorne APENAS o array JSON, sem texto adicional."""


def _build_classify_prompt(editais: list, perfis: dict) -> str:
    import re

    items = []
    for e in editais:
        comments = (e.get("comments") or "")
        valor_match = re.search(r'R\$\s*([\d.]+,\d{2})', comments)
        valor_pre = float(valor_match.group(1).replace(".", "").replace(",", ".")) if valor_match else None

        items.append({
            "id": e.get("id"),
            "title": e.get("title", ""),
            "description": (e.get("description") or "")[:250],
            "valor_extraido": valor_pre,
            "local": e.get("local", ""),
            "endDate": (e.get("endDate", "") or "")[:10],
            "receivingEmail": e.get("receivingEmail", ""),
        })

    return json.dumps({
        "perfis": {nome: {k: v for k, v in p.items() if k != "nome"}
                    for nome, p in perfis.items()},
        "editais": items,
    }, ensure_ascii=False, indent=2)


def _extrair_json(texto: str) -> dict | None:
    texto = texto.strip()
    if texto.startswith("```"):
        lines = texto.split("\n")
        texto = "\n".join(lines[1:-1])
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        start = texto.find("{")
        end = texto.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(texto[start:end])
            except json.JSONDecodeError:
                pass
    return None


def _call_deepseek(prompt: str, system: str, max_tokens: int = 16384) -> str | None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE)

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def analisar_com_ia(editais: list) -> dict | None:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.info("DEEPSEEK_API_KEY não configurada — usando análise determinística")
        return None

    try:
        from core.perfil import carregar_perfis
        perfis = carregar_perfis()

        prompt = _build_classify_prompt(editais, perfis)
        texto = _call_deepseek(prompt, CLASSIFY_PROMPT, max_tokens=32768)
        if not texto:
            return None

        logger.info("DeepSeek respondeu com %d caracteres", len(texto))
        resultado = _extrair_json(texto)
        if resultado is None:
            logger.warning("DeepSeek não retornou JSON válido. Início: %s", (texto or "")[:200])
            return None
        if isinstance(resultado, list):
            resultado = {"editais": resultado}

        return _processar_resposta(resultado, perfis, editais)

    except Exception as e:
        logger.warning("Erro ao usar DeepSeek: %s — usando análise determinística", e)
        return None


def _processar_resposta(resultado: dict, perfis: dict, raw_editais: list) -> dict:
    editais_data = resultado.get("editais", resultado.get("classificados", []))
    id_to_raw = {e.get("id"): e for e in raw_editais}

    classificados = []
    for ed in editais_data:
        eid = ed.get("id")
        raw = id_to_raw.get(eid, {})
        req = ed.get("requisitos", ed.get("requisitos_inferidos", {}))

        classificados.append({
            "id": eid,
            "torid": raw.get("torid", ed.get("torid", "")),
            "titulo": raw.get("title", ed.get("title", raw.get("titulo", ""))),
            "descricao": raw.get("description", ed.get("description", "")),
            "tipo": ed.get("tipo", "Consultoria (tipo não especificado)"),
            "areas_tematicas": ed.get("areas_tematicas", []),
            "data_inicio": (raw.get("startDate", "") or "")[:10],
            "data_fim": (raw.get("endDate", "") or ed.get("endDate", "") or "")[:10],
            "local": raw.get("local", ed.get("local", "")),
            "orgao_parceiro": ed.get("orgao_parceiro", "Não identificado"),
            "email_submissao": raw.get("receivingEmail", ed.get("receivingEmail", "")),
            "valor_estimado": _format_valor(ed.get("valor_estimado_num")),
            "valor_estimado_num": ed.get("valor_estimado_num"),
            "status": ed.get("status", raw.get("statusDescription", "Aprovada")),
            "data_criacao": (raw.get("created", "") or "")[:10],
            "perfil_classificado": ed.get("perfil_classificado", "Não classificado"),
            "requisitos": {
                "graduacao": req.get("graduacao", []),
                "ferramentas": req.get("ferramentas", []),
                "idiomas": req.get("idiomas", []),
                "anos_experiencia": req.get("anos_experiencia"),
                "mestrado": req.get("mestrado", False),
                "doutorado": req.get("doutorado", False),
                "pos_graduacao": req.get("pos_graduacao", []),
                "certificacoes": req.get("certificacoes", []),
                "valor_tor": None,
                "obrigatorios": req.get("obrigatorios", []),
                "desejaveis": req.get("desejaveis", []),
            },
        })

    for ec in classificados:
        matches_raw = {}
        for ed in editais_data:
            if ed.get("id") == ec["id"]:
                matches_raw = ed.get("matches", ed.get("match", {}))
                break

        ec["matches"] = {}
        for nome_perfil in perfis:
            m = matches_raw.get(nome_perfil, {})
            ec["matches"][nome_perfil] = {
                "score": m.get("score", 0),
                "detalhes": {
                    "areas": {"match": m.get("areas", False), "encontradas": []},
                    "ferramentas": {
                        "match": m.get("ferramentas_match", []),
                        "faltando": m.get("ferramentas_faltando", []),
                        "exigidas": ec.get("requisitos", {}).get("ferramentas", []),
                    },
                    "graduacao": {
                        "match": m.get("graduacao_match", []),
                        "exigidas": ec.get("requisitos", {}).get("graduacao", []),
                    },
                    "idiomas": {
                        "match": m.get("idiomas_match", []),
                        "exigidos": ec.get("requisitos", {}).get("idiomas", []),
                    },
                    "valor": {
                        "edital": ec.get("valor_estimado_num"),
                        "minimo_perfil": perfis.get(nome_perfil, {}).get("valor_minimo", 0),
                        "acima_minimo": (ec.get("valor_estimado_num") or 0) >= perfis.get(nome_perfil, {}).get("valor_minimo", 0),
                    },
                },
            }
        ec["url_externo"] = "https://parceiros.undp.org.br/opportunities"

    recom = {}
    try:
        recom = _gerar_recomendacoes_ia(classificados, perfis)
    except Exception as e:
        logger.warning("Recomendações IA falharam: %s", e)

    perfis_list = []
    for nome, perfil in perfis.items():
        count = sum(1 for e in classificados if e["matches"].get(nome, {}).get("score", 0) >= 0.15)
        perfis_list.append({
            "nome": nome, "descricao": perfil.get("descricao", ""),
            "graduacoes": perfil.get("graduacoes", []),
            "ferramentas": perfil.get("ferramentas", []),
            "areas_interesse": perfil.get("areas_interesse", []),
            "idiomas": perfil.get("idiomas", []),
            "match_count": count,
        })

    contagem_tipos = Counter(e["tipo"] for e in classificados)
    contagem_orgaos = Counter(e["orgao_parceiro"] for e in classificados)
    areas_flat = []
    for e in classificados:
        a = e.get("areas_tematicas", [])
        areas_flat.extend(a if isinstance(a, list) else [a])
    contagem_areas = Counter(areas_flat)
    valores = [e["valor_estimado_num"] for e in classificados if e.get("valor_estimado_num")]

    return {
        "gerado_em": None,
        "resumo": {
            "total_editais": len(classificados),
            "novos_hoje": 0, "encerrados_hoje": 0,
            "por_tipo": dict(contagem_tipos.most_common()),
            "por_area": dict(contagem_areas.most_common(10)),
            "por_orgao": dict(contagem_orgaos.most_common()),
            "valores": {
                "minimo": min(valores) if valores else None,
                "maximo": max(valores) if valores else None,
                "medio": sum(valores) / len(valores) if valores else None,
                "mediano": sorted(valores)[len(valores) // 2] if valores else None,
                "quantidade_com_valor": len(valores),
            },
        },
        "perfis": perfis_list,
        "editais": classificados,
        "recomendacoes": recom,
        "modo": "ia",
    }


RECOMMEND_PROMPT = """Gere recomendações de estudo para um perfil profissional com base nos editais analisados.
Retorne APENAS JSON com:

"curto_prazo": [{"gap": "...", "curso": "...", "custo": "...", "carga": "...", "link": "..."}]
"medio_prazo": [{"gap": "...", "curso": "...", "custo": "...", "carga": "...", "link": "..."}]
"longo_prazo": [{"gap": "...", "curso": "...", "custo": "...", "carga": "...", "link": "..."}]

Curto: 3-6 meses (certificações, cursos rápidos). Médio: 6-18 meses (especializações). Longo: 1-3 anos (mestrado/doutorado).
Inclua links reais quando souber (Microsoft Learn, Coursera, ENAP, Udemy, UFBA, INPE, ESRI)."""


def _gerar_recomendacoes_ia(classificados: list, perfis: dict) -> dict:
    recomendacoes = {}
    for nome_perfil, perfil in perfis.items():
        compativeis = [e for e in classificados if e["matches"].get(nome_perfil, {}).get("score", 0) >= 0.15]
        if not compativeis:
            recomendacoes[nome_perfil] = _recom_vazio(nome_perfil, perfil, len(classificados))
            continue

        gaps = _extrair_gaps(compativeis, perfil)
        prompt = json.dumps({
            "perfil": nome_perfil,
            "descricao": perfil.get("descricao", ""),
            "ferramentas_perfil": perfil.get("ferramentas", []),
            "graduacoes_perfil": perfil.get("graduacoes", []),
            "gaps_identificados": {k: list(v.most_common(6)) for k, v in gaps.items()},
            "total_editais_compativeis": len(compativeis),
        }, ensure_ascii=False, indent=2)

        texto = _call_deepseek(prompt, RECOMMEND_PROMPT, max_tokens=4096)
        rec_data = _extrair_json(texto) if texto else {}

        valor_total = sum(e.get("valor_estimado_num") or 0 for e in compativeis)
        recomendacoes[nome_perfil] = {
            "perfil": nome_perfil,
            "descricao": perfil.get("descricao", ""),
            "total_editais_analisados": len(classificados),
            "total_editais_compativeis": len(compativeis),
            "valor_total_oportunidades": round(valor_total, 2),
            "periodo_analise": "Últimos 12 meses (DeepSeek)",
            "curto_prazo": {"gaps": [], "plano": rec_data.get("curto_prazo", [])},
            "medio_prazo": {"gaps": [], "plano": rec_data.get("medio_prazo", [])},
            "longo_prazo": {"gaps": [], "plano": rec_data.get("longo_prazo", [])},
        }

    return recomendacoes


def _extrair_gaps(editais: list, perfil: dict) -> dict:
    from collections import Counter
    perfil_ferr = set(f.lower() for f in perfil.get("ferramentas", []))
    perfil_grad = set(g.lower() for g in perfil.get("graduacoes", []))
    perfil_lang = set(l.lower() for l in perfil.get("idiomas", []))

    ferr = Counter()
    grad = Counter()
    lang = Counter()
    for e in editais:
        req = e.get("requisitos", {})
        for f in req.get("ferramentas", []):
            if f.lower() not in perfil_ferr:
                ferr[f.lower()] += 1
        for g in req.get("graduacao", []):
            if not any(pg in g.lower() or g.lower() in pg for pg in perfil_grad):
                grad[g.lower()] += 1
        for l in req.get("idiomas", []):
            if l.lower() not in perfil_lang:
                lang[l.lower()] += 1

    return {"ferramentas": ferr, "graduacoes": grad, "idiomas": lang}


def _recom_vazio(nome: str, perfil: dict, total: int) -> dict:
    return {
        "perfil": nome, "descricao": perfil.get("descricao", ""),
        "total_editais_analisados": total, "total_editais_compativeis": 0,
        "valor_total_oportunidades": 0,
        "periodo_analise": "Últimos 12 meses (DeepSeek)",
        "curto_prazo": {"gaps": [], "plano": []},
        "medio_prazo": {"gaps": [], "plano": []},
        "longo_prazo": {"gaps": [], "plano": []},
    }


def _format_valor(v):
    if v is None:
        return None
    return f"R$ {v:,.2f}".replace(".", ",")
