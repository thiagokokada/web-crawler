from urllib import parse
from typing import AnyStr, Dict, List, Iterable

from bs4 import BeautifulSoup

from web_crawler.models import status


def same_host(base_url: str, current_url: str) -> bool:
    return current_url.startswith(base_url)


def filter_url(url: str) -> str:
    parsed_url = parse.urlparse(url)

    # Remove trailing / from path
    if parsed_url.path.endswith("/"):
        path = parsed_url.path[:-1]
    else:
        path = parsed_url.path

    return f"{parsed_url.scheme}://{parsed_url.netloc}{path}"


def get_url(base_url: str, url_or_path: str) -> str:
    if parse.urlparse(url_or_path).scheme == "":
        final_url = parse.urljoin(base_url, url_or_path)
    else:
        final_url = url_or_path

    return filter_url(final_url)


def find_urls(base_url: str, html: AnyStr) -> List[str]:
    parsed_html = BeautifulSoup(html, "html.parser")

    # Using a dict here since we want to ignore duplicate values,
    # but we want to keep the insertion order
    # (that is guarantee in dicts since Python 3.7).
    urls: Dict[str, None] = {}
    for tag in parsed_html.find_all("a", href=True):
        href = tag.get("href")
        # Ignore, this is used only by JS
        if href == "#":
            continue
        if tag.name == "a":
            url = get_url(base_url, href)
            urls[url] = None

    return list(urls.keys())


def urls_to_crawl(
    base_url: str,
    found_urls: List[str],
    crawled_urls: Iterable[str],
) -> List[str]:
    return [
        url
        for url in found_urls
        if url not in crawled_urls and same_host(base_url, url)
    ]


def url_status(
    found_url: str,
    base_url: str,
    crawled_urls: Iterable[str],
) -> status.WebCrawlerStatus:
    if found_url in crawled_urls:
        return status.AlreadyCrawled()
    elif not found_url.startswith(("http://", "https://")):
        return status.InvalidProtocol()
    elif not same_host(base_url, found_url):
        return status.DifferentHost()
    else:
        # This is not exactly true since the recursive limit can be further
        # below, # but in this case the dict for this entry will be updated
        # later on after the recursively crawling part
        return status.DepthLimit()
