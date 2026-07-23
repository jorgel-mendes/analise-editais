"""
Script para extrair dados dos editais do PNUD Brasil via parceiros.undp.org.br/opportunities
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent / "dados_brutos"
OUTPUT_DIR.mkdir(exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # Coletar todas as requisições de rede
        network_requests = []

        async def handle_request(request):
            url = request.url
            method = request.method
            headers = request.headers
            network_requests.append({
                "url": url,
                "method": method,
                "type": request.resource_type
            })

        async def handle_response(response):
            url = response.url
            if "api" in url.lower() or "icnim" in url.lower() or "dsa" in url.lower():
                try:
                    body = await response.text()
                    if body and len(body) < 50000:
                        name = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_").replace("=", "_")[:100]
                        filepath = OUTPUT_DIR / f"response_{name}.json"
                        try:
                            data = json.loads(body)
                            filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
                            print(f"  [API] {method} {url[:120]} -> {len(body)} bytes (JSON)")
                        except (json.JSONDecodeError, ValueError):
                            filepath = OUTPUT_DIR / f"response_{name}.txt"
                            filepath.write_text(body)
                            print(f"  [API] {method} {url[:120]} -> {len(body)} bytes (text)")
                except Exception as e:
                    print(f"  [API ERROR] {url[:120]}: {e}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        print("=" * 60)
        print("Navegando para https://parceiros.undp.org.br/opportunities ...")
        print("=" * 60)

        try:
            await page.goto("https://parceiros.undp.org.br/opportunities", wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"Timeout/erro no carregamento: {e}")
            await page.wait_for_timeout(10000)

        # Esperar a página carregar
        await page.wait_for_timeout(5000)

        # Tirar screenshot
        await page.screenshot(path=str(OUTPUT_DIR / "screenshot.png"), full_page=True)
        print("Screenshot salva em dados_brutos/screenshot.png")

        # Pegar o HTML renderizado
        html_content = await page.content()
        (OUTPUT_DIR / "page.html").write_text(html_content)
        print(f"HTML salvo ({len(html_content)} bytes)")

        # Listar todos os links na página
        all_text = await page.inner_text("body")
        (OUTPUT_DIR / "page_text.txt").write_text(all_text)
        print(f"Texto da página salvo ({len(all_text)} bytes)")

        # Tentar clicar em elementos de navegação
        print("\n--- Tentando encontrar links DSA ---")
        try:
            # Tentar encontrar links na navegação lateral (Fuse vertical navigation)
            nav_items = await page.query_selector_all(".fuse-vertical-navigation-item")
            print(f"Encontrados {len(nav_items)} itens de navegação")

            for i, item in enumerate(nav_items):
                text = await item.inner_text()
                print(f"  [{i}] {text.strip()[:200]}")
        except Exception as e:
            print(f"Erro ao buscar navegação: {e}")

        # Tentar encontrar cards/cards de oportunidade
        try:
            cards = await page.query_selector_all("mat-card, .card, .opportunity-card, dsa-card")
            print(f"\nEncontrados {len(cards)} cards")
        except:
            pass

        # Tentar encontrar iframes
        try:
            iframes = await page.query_selector_all("iframe")
            print(f"\nEncontrados {len(iframes)} iframes")
            for i, iframe in enumerate(iframes):
                src = await iframe.get_attribute("src")
                print(f"  iframe[{i}] src={src}")
        except:
            pass

        # Pegar localStorage e sessionStorage
        local_storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
        session_storage = await page.evaluate("() => JSON.stringify(window.sessionStorage)")
        (OUTPUT_DIR / "localStorage.json").write_text(local_storage)
        (OUTPUT_DIR / "sessionStorage.json").write_text(session_storage)

        # Resumo de todas as requisições de rede
        print(f"\n--- Resumo das requisições de rede ({len(network_requests)} total) ---")
        api_requests = [r for r in network_requests if "api" in r["url"].lower() or "icnim" in r["url"].lower()]
        for r in api_requests:
            print(f"  {r['method']} {r['url'][:150]}")

        (OUTPUT_DIR / "network_requests.json").write_text(
            json.dumps(network_requests, indent=2, ensure_ascii=False)
        )
        print(f"\nRequisições salvas em dados_brutos/network_requests.json")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
