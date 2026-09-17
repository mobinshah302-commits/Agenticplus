"""
وب‌سرچ رایگان بدون نیاز به API key، با اسکرپ نسخه‌ی HTML داک‌داک‌گو (پایدارتر از اسکرپ گوگل
و بدون کپچا). خروجی: تیتر + خلاصه + لینک برای هر نتیجه.
"""
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


async def search(query: str, max_results: int = 5) -> list[dict]:
    url = "https://html.duckduckgo.com/html/"
    async with httpx.AsyncClient(timeout=20.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.post(url, data={"q": query})
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for result in soup.select(".result")[:max_results]:
        title_el = result.select_one(".result__a")
        snippet_el = result.select_one(".result__snippet")
        if not title_el:
            continue
        results.append({
            "title": title_el.get_text(strip=True),
            "url": title_el.get("href", ""),
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
        })
    return results


async def fetch_page_text(url: str, max_chars: int = 6000) -> str:
    """برای ابزار مرورگر: گرفتن متن خام یک صفحه (بدون رندر جاوااسکریپت)."""
    async with httpx.AsyncClient(timeout=25.0, headers=HEADERS, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars]
