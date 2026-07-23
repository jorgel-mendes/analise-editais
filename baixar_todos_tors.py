"""
Baixar TODOS os Termos de Referência disponíveis no portal PNUD
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent / "dados_brutos" / "tors"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
        )
        page = await context.new_page()

        downloads = []

        async def handle_download(download):
            filename = download.suggested_filename
            path = OUTPUT_DIR / filename
            await download.save_as(str(path))
            downloads.append(filename)
            print(f"  Download: {filename} ({path.stat().st_size} bytes)")

        page.on("download", handle_download)

        print("Navegando para oportunidades...")
        await page.goto(
            "https://parceiros.undp.org.br/opportunities",
            wait_until="networkidle",
            timeout=60000,
        )
        await page.wait_for_timeout(3000)

        rows = await page.query_selector_all("mat-row")
        print(f"Total de editais para baixar: {len(rows)}")

        for i, row in enumerate(rows):
            try:
                text = (await row.inner_text()).strip()
                title_line = text.split("\n")[0][:100]
                
                # Clicar no botão de download
                download_cell = await row.query_selector("mat-cell:last-child button")
                if download_cell:
                    await download_cell.click()
                    await page.wait_for_timeout(2000)
                    print(f"  [{i+1}/{len(rows)}] {title_line}...")
                else:
                    print(f"  [{i+1}/{len(rows)}] SEM BOTÃO: {title_line}...")
            except Exception as e:
                print(f"  [{i+1}/{len(rows)}] ERRO: {e}")

        print(f"\nTotal downloads: {len(downloads)}")
        for d in downloads:
            print(f"  {d}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
