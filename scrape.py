from googlesearch import search
from urllib.parse import urlparse
from goose3 import Goose
from goose3.configuration import Configuration
from playwright.async_api import async_playwright
import asyncio

def get_domain(url):
    return urlparse(url).netloc.lower()

async def scrape_articles(query: str, valid_domains: list):
    urls = []
    for url in search(query, num_results=20):
        domain = get_domain(url)
        if any(domain.endswith(valid) for valid in valid_domains):
            if url not in urls:
                urls.append(url)

    failed = []

    config = Configuration()
    config.browser_user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    g = Goose({'browser_user_agent': config.browser_user_agent})
    results = []

    for url in urls:
        try:
            article = g.extract(url=url)
            content = article.cleaned_text.strip() if article.cleaned_text else ""
            if content:
                results.append({
                    "Title": article.title or "N/A",
                    "Authors": article.authors or [],
                    "Published Date": article.publish_date or "N/A",
                    "Content": content,
                    "URL": url
                })
            else:
                failed.append(url)
        except Exception:
            failed.append(url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for url in failed:
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=20000)
                await page.wait_for_load_state('domcontentloaded')
                title = await page.title()
                content_blocks = await page.locator("article").all_inner_texts()
                content = "\n".join(content_blocks).strip()
                if not content:
                    paragraphs = await page.locator("p").all_inner_texts()
                    content = "\n".join(paragraphs).strip()
                if content:
                    results.append({
                        "Title": title or "N/A",
                        "Authors": [],
                        "Published Date": "N/A",
                        "Content": content,
                        "URL": url,
                    })
                await page.close()
            except:
                continue
        await browser.close()

    return results
