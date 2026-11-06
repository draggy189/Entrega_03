"""Web scraping de un sitio estático."""
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

MAX_BYTES = 5_000_000


def url_valida(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)


def obtener_texto(url: str) -> str:
    """Descarga la página y devuelve su texto plano."""
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    if "html" not in r.headers.get("Content-Type", "").lower():
        raise ValueError("La URL no devuelve una página HTML.")
    if len(r.content) > MAX_BYTES:
        raise ValueError("La página es demasiado grande (máx. 5 MB).")
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, "html.parser")
    for etiqueta in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        etiqueta.decompose()
    return " ".join(soup.get_text(separator=" ").split())