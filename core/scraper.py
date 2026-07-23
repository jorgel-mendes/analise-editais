import asyncio
import json
from datetime import date

from core.config import API_URL, API_ENDPOINT
from core.persistence import salvar_snapshot, atualizar_editais_todos, detectar_novidades, carregar_ultimo_snapshot


async def _scrape_async() -> list:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        captured_data = []

        async def handle_response(response):
            url = response.url
            if "api" in url.lower() and API_ENDPOINT in url:
                try:
                    body = await response.text()
                    if body and len(body) < 200000:
                        try:
                            data = json.loads(body)
                            if isinstance(data, list):
                                captured_data.extend(data)
                            elif isinstance(data, dict):
                                results = data.get("data") or data.get("results") or []
                                if isinstance(results, list):
                                    captured_data.extend(results)
                        except (json.JSONDecodeError, ValueError):
                            pass
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(API_URL, wait_until="networkidle", timeout=60000)
        except Exception:
            await page.wait_for_timeout(10000)

        await page.wait_for_timeout(5000)
        await browser.close()

    return captured_data


def executar_scraping() -> tuple[list, dict | None]:
    """Executa scraping e retorna os editais atuais + resumo de novidades."""
    print("🔍 Buscando editais do PNUD Brasil...")
    editais_atuais = asyncio.run(_scrape_async())

    if not editais_atuais:
        print("⚠️  Nenhum edital encontrado no scraping.")
        return [], None

    hoje = date.today()
    snapshot_file = salvar_snapshot(editais_atuais, hoje)
    print(f"💾 Snapshot salvo em: {snapshot_file}")

    novos, atualizados = atualizar_editais_todos(editais_atuais)
    print(f"📊 {novos} novos, {atualizados} atualizados, {len(editais_atuais)} ativos no total")

    anteriores = carregar_ultimo_snapshot()
    if anteriores and anteriores != editais_atuais:
        novidades = detectar_novidades(editais_atuais, anteriores)
        if novidades["novos_count"] > 0 or novidades["encerrados_count"] > 0:
            print(f"🆕 {novidades['novos_count']} editais novos")
            print(f"🔒 {novidades['encerrados_count']} editais encerrados")
            return editais_atuais, novidades

    return editais_atuais, None
