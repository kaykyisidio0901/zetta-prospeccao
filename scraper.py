import re
import json
import urllib.request
import urllib.parse


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def raspar_google_maps(url_busca: str, max_resultados=15):
    resultados = []

    parsed = urllib.parse.urlparse(url_busca)
    params = urllib.parse.parse_qs(parsed.query)
    query = params.get("search", params.get("query", [""]))[0]

    if not query:
        query = url_busca

    search_url = "https://www.google.com/maps/search/" + urllib.parse.quote(query)
    req = urllib.request.Request(search_url, headers=_HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar Google Maps: {e}")

    pattern = r'\["(.*?)",\s*\[\[(?:\[.*?\],?\s*){1,2}(?:null|"[^"]*")\],?\s*"([^"]*)"[^,]*,\s*\[null,\s*\[(\d+\.\d+),\s*(\-?\d+\.\d+)\]'
    matches = re.findall(pattern, html)

    seen = set()
    for nome, telefone_raw, lat, lng in matches:
        if not nome or nome in seen or len(nome) < 2:
            continue
        if nome.startswith("http") or nome.startswith("/"):
            continue
        telefone = re.sub(r"\D", "", telefone_raw) if telefone_raw else ""
        seen.add(nome)
        resultados.append({
            "nome": nome,
            "telefone": telefone,
            "site": "",
            "lat": float(lat),
            "lng": float(lng),
        })
        if len(resultados) >= max_resultados:
            break

    if not resultados:
        data_pattern = r'\[null,null,(\d+\.?\d*),(\-?\d+\.?\d*)\]'
        geo_matches = re.findall(data_pattern, html)

        name_pattern = r'class="fontHeadlineSmall[^"]*"[^>]*>([^<]+)<'
        names = re.findall(name_pattern, html)

        phone_pattern = r'(?:\(\d{2}\)\s*\d{4,5}-\d{4}|\d{2}\s*\d{4,5}-\d{4})'
        phones = re.findall(phone_pattern, html)

        for i, nome in enumerate(names):
            if not nome or nome in seen or len(nome) < 2:
                continue
            seen.add(nome)
            telefone = re.sub(r"\D", "", phones[i]) if i < len(phones) else ""
            resultados.append({
                "nome": nome.strip(),
                "telefone": telefone,
                "site": "",
            })
            if len(resultados) >= max_resultados:
                break

    return resultados
