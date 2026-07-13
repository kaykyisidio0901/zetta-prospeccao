import re
import random
import time

from playwright.sync_api import sync_playwright


_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
]


def _extrair_telefone_e_site(page):
    telefone = ""
    site = ""

    try:
        page.wait_for_selector('[aria-label^="Telefone:" i]', timeout=8000)
        for el in page.query_selector_all('[aria-label^="Telefone:" i]'):
            texto = el.get_attribute("aria-label") or ""
            match = re.search(r"[\d\s()-]{8,}", texto)
            if match:
                telefone = re.sub(r"\D", "", match.group())
                break
    except Exception:
        try:
            page.wait_for_selector('button[data-item-id*="phone"]', timeout=5000)
            for el in page.query_selector_all('button[data-item-id*="phone"]'):
                aria = el.get_attribute("aria-label") or ""
                match = re.search(r"[\d\s()-]{8,}", aria)
                if match:
                    telefone = re.sub(r"\D", "", match.group())
                    break
        except Exception:
            texto_completo = page.inner_text("body")
            match = re.search(r"\(\d{2}\)\s*\d{4,5}-\d{4}", texto_completo)
            if match:
                telefone = re.sub(r"\D", "", match.group())

    for el in page.query_selector_all("a"):
        href = el.get_attribute("href") or ""
        txt = el.inner_text().strip()
        if href.startswith(("http://", "https://")) and "google" not in href and "maps" not in href:
            if txt and not href.endswith((".jpg", ".png", ".svg")):
                site = href
                break

    return telefone, site


def raspar_google_maps(url_busca: str, max_resultados=15):
    resultados = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=random.choice(_USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
        )
        page = context.new_page()

        page.goto(url_busca, timeout=40000)
        page.wait_for_timeout(4000)

        for tentativa in range(6):
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1500 + int(random.random() * 1000))

        cards = page.query_selector_all('a[href*="/maps/place/"]')
        vistos = set()
        links_coletados = []

        for card in cards:
            try:
                nome = card.inner_text().strip().split("\n")[0].strip()
                href = card.get_attribute("href") or ""
                if nome and not nome.startswith("http") and href not in vistos:
                    vistos.add(href)
                    links_coletados.append((nome, href))
            except Exception:
                continue

        for nome, href in links_coletados[:max_resultados]:
            try:
                page.goto(href, timeout=20000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                telefone, site = _extrair_telefone_e_site(page)
            except Exception:
                telefone, site = "", ""

            resultados.append({
                "nome": nome,
                "telefone": telefone,
                "site": site,
            })

        browser.close()

    return resultados
