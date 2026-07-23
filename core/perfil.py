import json
from pathlib import Path

from core.config import PERFIS_DIR


def carregar_perfis() -> dict[str, dict]:
    perfis = {}
    if PERFIS_DIR.exists():
        for arquivo in PERFIS_DIR.glob("*.json"):
            nome = arquivo.stem
            try:
                perfis[nome] = json.loads(arquivo.read_text())
            except (json.JSONDecodeError, KeyError):
                pass
    return perfis


def carregar_perfil(nome: str) -> dict | None:
    arquivo = PERFIS_DIR / f"{nome}.json"
    if arquivo.exists():
        return json.loads(arquivo.read_text())
    return None


def salvar_perfil(nome: str, dados: dict) -> Path:
    PERFIS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = PERFIS_DIR / f"{nome}.json"
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False))
    return caminho


def pontuar_edital_para_perfil(edital: dict, perfil: dict) -> float:
    """Calcula uma pontuação de compatibilidade (0.0 a 1.0) entre um edital e um perfil."""
    score = 0.0
    peso_maximo = 0.0

    areas_edital = edital.get("areas_tematicas", "")
    if areas_edital:
        areas_interesse = set(perfil.get("areas_interesse", []))
        areas_str = areas_edital if isinstance(areas_edital, str) else ", ".join(areas_edital)
        for area in areas_interesse:
            if area.lower() in areas_str.lower():
                score += 0.30
                break
    peso_maximo += 0.30

    ferramentas_edital = [f.lower() for f in edital.get("ferramentas", [])]
    ferramentas_perfil = [f.lower() for f in perfil.get("ferramentas", [])]
    if ferramentas_edital and ferramentas_perfil:
        matches = set(ferramentas_edital) & set(ferramentas_perfil)
        if matches:
            score += 0.25 * (len(matches) / max(len(ferramentas_perfil), 1))
    peso_maximo += 0.25

    graduacoes_edital = [g.lower() for g in edital.get("graduacao", [])]
    graduacoes_perfil = [g.lower() for g in perfil.get("graduacoes", [])]
    if graduacoes_edital and graduacoes_perfil:
        matches = set(graduacoes_edital) & set(graduacoes_perfil)
        if matches:
            score += 0.25 * (len(matches) / max(len(graduacoes_perfil), 1))
    peso_maximo += 0.25

    idiomas_edital = [i.lower() for i in edital.get("idiomas", [])]
    idiomas_perfil = [i.lower() for i in perfil.get("idiomas", [])]
    if idiomas_edital and idiomas_perfil:
        matches = set(idiomas_edital) & set(idiomas_perfil)
        if matches:
            score += 0.10 * (len(matches) / len(idiomas_edital))
    peso_maximo += 0.10

    valor_edital = edital.get("valor_estimado_num", 0)
    valor_minimo = perfil.get("valor_minimo", 0)
    if valor_edital and valor_minimo:
        if valor_edital >= valor_minimo:
            score += 0.10
        else:
            score += 0.05 * (valor_edital / valor_minimo)
    peso_maximo += 0.10

    if peso_maximo > 0:
        score = score / peso_maximo

    return round(score, 3)


def classificar_perfil_do_edital(edital: dict) -> str:
    """Determina o perfil mais compatível com um edital usando todos os perfis disponíveis."""
    perfis = carregar_perfis()
    if not perfis:
        return "Não classificado"

    melhor_perfil = None
    melhor_pontuacao = 0.0

    for nome, perfil in perfis.items():
        pontuacao = pontuar_edital_para_perfil(edital, perfil)
        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_perfil = nome

    if melhor_pontuacao >= 0.15:
        return melhor_perfil
    return "Não classificado"


def filtrar_por_perfil(editais: list, nome_perfil: str) -> list:
    """Filtra editais que correspondem a um perfil específico."""
    perfil = carregar_perfil(nome_perfil)
    if not perfil:
        return []

    resultado = []
    for edital in editais:
        pontuacao = pontuar_edital_para_perfil(edital, perfil)
        if pontuacao >= 0.15:
            resultado.append({**edital, "score_perfil": pontuacao})
    return sorted(resultado, key=lambda e: e["score_perfil"], reverse=True)
