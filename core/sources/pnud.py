"""Fonte PNUD Brasil — scraping via Playwright (SPA que só expõe os dados por API interna)."""
import asyncio
import json

from core.config import API_URL, API_ENDPOINT


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


def _normalizar(raw: dict) -> dict:
    """O formato bruto do PNUD já é o formato canônico interno do pipeline —
    só adiciona os campos de fonte/link que os outros scrapers também produzem."""
    return {
        **raw,
        "fonte": "pnud",
        "url_externo": API_URL,
    }


def buscar_ativos() -> list[dict]:
    """Busca os editais atualmente ativos no portal do PNUD Brasil."""
    dados = asyncio.run(_scrape_async())
    return [_normalizar(e) for e in dados]
