from datetime import date

from core.config import FONTES_DISPONIVEIS
from core.persistence import salvar_snapshot, atualizar_editais_todos, detectar_novidades, carregar_ultimo_snapshot
from core.sources import oei, pnud, unesco

_BUSCADORES = {
    "pnud": pnud.buscar_ativos,
    "unesco": unesco.buscar_ativos,
    "oei": oei.buscar_ativos,
}


def executar_scraping(fontes: list[str] | None = None) -> tuple[list, dict | None]:
    """Executa scraping das fontes selecionadas e retorna os editais atuais + resumo de novidades."""
    fontes = fontes or FONTES_DISPONIVEIS

    editais_atuais = []
    fontes_ok = []
    for nome in fontes:
        buscar = _BUSCADORES.get(nome)
        if not buscar:
            print(f"⚠️  Fonte desconhecida: {nome}")
            continue
        print(f"🔍 Buscando editais da fonte '{nome}'...")
        try:
            resultado = buscar()
        except Exception as e:
            print(f"❌ Falha ao buscar '{nome}': {e} — fonte ignorada nesta execução")
            continue
        print(f"   {len(resultado)} edital(is) encontrado(s)")
        editais_atuais.extend(resultado)
        fontes_ok.append(nome)

    if not editais_atuais:
        print("⚠️  Nenhum edital encontrado no scraping.")
        return [], None

    anteriores_completos = carregar_ultimo_snapshot()

    # Só compara com fontes que de fato rodaram nesta execução — senão uma
    # falha pontual numa fonte faria seus editais anteriores parecerem
    # "encerrados" por engano.
    anteriores = [e for e in anteriores_completos if e.get("fonte", "pnud") in fontes_ok]

    # Fontes que falharam nesta execução entram no snapshot de hoje do jeito
    # que estavam ontem, senão "reaparecem" como falso-novo quando a fonte
    # voltar a funcionar.
    fontes_falhas = set(fontes) - set(fontes_ok)
    preservados = [e for e in anteriores_completos if e.get("fonte", "pnud") in fontes_falhas]

    hoje = date.today()
    snapshot_file = salvar_snapshot(editais_atuais + preservados, hoje)
    print(f"💾 Snapshot salvo em: {snapshot_file}")

    novos, atualizados = atualizar_editais_todos(editais_atuais)
    print(f"📊 {novos} novos, {atualizados} atualizados, {len(editais_atuais)} ativos no total")

    if anteriores and anteriores != editais_atuais:
        novidades = detectar_novidades(editais_atuais, anteriores)
        if novidades["novos_count"] > 0 or novidades["encerrados_count"] > 0:
            print(f"🆕 {novidades['novos_count']} editais novos")
            print(f"🔒 {novidades['encerrados_count']} editais encerrados")
            return editais_atuais, novidades

    return editais_atuais, None
