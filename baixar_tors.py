"""
Baixar Termos de Referência específicos clicando nos botões de download
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
            downloads.append((filename, str(path), path.stat().st_size))
            print(f"  >> DOWNLOAD: {filename} ({path.stat().st_size} bytes)")

        page.on("download", handle_download)

        print("Navegando para oportunidades...")
        await page.goto(
            "https://parceiros.undp.org.br/opportunities",
            wait_until="networkidle",
            timeout=60000,
        )
        await page.wait_for_timeout(3000)

        # Encontrar todas as linhas da tabela
        rows = await page.query_selector_all("mat-row")
        print(f"Linhas na tabela: {len(rows)}")

        for i, row in enumerate(rows):
            text = (await row.inner_text()).strip()
            # Filtrar: Edital 11/2026 (BI) e Edital 10/2026 (Dimensionamento)
            if "Edital nº 11/2026" in text or "Edital nº 10/2026" in text:
                print(f"\nLinha {i}: {text[:120]}...")
                # Clicar no botão de download (última célula)
                download_cell = await row.query_selector("mat-cell:last-child")
                if download_cell:
                    # Tentar encontrar botão ou link dentro
                    btn = await download_cell.query_selector("button, a, mat-icon, .mat-icon")
                    if btn:
                        print(f"  Clicando botão de download...")
                        await btn.click()
                        await page.wait_for_timeout(3000)
                    else:
                        # Clicar na própria célula
                        print(f"  Clicando célula de download...")
                        await download_cell.click()
                        await page.wait_for_timeout(3000)

        # Também tentar achar elementos específicos de download
        print("\n--- Procurando elementos clickáveis de download ---")
        
        # Buscar por mat-icon ou botões
        icons = await page.query_selector_all("mat-icon, button[mat-icon-button]")
        print(f"Ícones/botões: {len(icons)}")
        
        # Procurar especificamente na linha do Edital 11
        edital_11_cell = await page.query_selector("text=Edital nº 11/2026")
        if edital_11_cell:
            # Subir para a linha (mat-row)
            parent_row = await edital_11_cell.evaluate_handle("""el => {
                let p = el;
                while (p && p.tagName !== 'MAT-ROW') p = p.parentElement;
                return p;
            }""")
            if parent_row:
                row_html = await parent_row.evaluate("el => el.innerHTML")
                print(f"\nHTML da linha do Edital 11:")
                print(row_html[:2000])

                # Tentar encontrar e clicar no botão de download
                download_btn = await parent_row.query_selector("button, a, mat-icon")
                if download_btn:
                    print("  Clicando botão na linha...")
                    await download_btn.click()
                    await page.wait_for_timeout(5000)

        # Verificar localStorage por tokens
        local_storage = await page.evaluate("() => JSON.stringify(window.localStorage)")
        if len(local_storage) > 10:
            print(f"\nlocalStorage: {local_storage[:500]}")
        
        # Mostrar todos os downloads
        if downloads:
            print(f"\n--- Downloads realizados: {len(downloads)} ---")
            for fname, fpath, fsize in downloads:
                print(f"  {fname}: {fsize} bytes -> {fpath}")
        else:
            print("\nNenhum download capturado. Tentando via API com headers...")
            # Tentar obter headers da página
            headers = await page.evaluate("""() => {
                // Tentar acessar a API com fetch
                return 'tentando...';
            }""")
            
            # Tentar download via fetch API dentro do browser
            for torid in [146152, 146148]:
                result = await page.evaluate("""async (torid) => {
                    try {
                        const resp = await fetch('https://icnim-api.undp.org.br/icnim/v1/Dsa?file=' + torid, {
                            method: 'GET',
                            credentials: 'include',
                        });
                        if (resp.ok) {
                            const blob = await resp.blob();
                            return {ok: true, size: blob.size, type: blob.type};
                        }
                        return {ok: false, status: resp.status};
                    } catch(e) {
                        return {error: e.message};
                    }
                }""", torid)
                print(f"  Fetch API torid={torid}: {result}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
