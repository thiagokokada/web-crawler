import asyncio
import logging
from concurrent import futures
from typing import Dict, List, Optional, Set

import httpx

from web_crawler.logic import crawl


class Crawler:
    def __init__(self, depth_limit: int = 2, workers: int = 10):
        self.depth_limit = depth_limit
        # Crawler constructor should be called inside a async context,
        # or it will fail
        self.loop = asyncio.get_running_loop()
        self.semaphore = asyncio.Semaphore(workers)
        self.executor = futures.ProcessPoolExecutor(max_workers=workers)
        self.client = httpx.AsyncClient()

    def __del__(self):
        asyncio.create_task(self.client.aclose())
        self.executor.shutdown()

    async def crawl_url(self, target_url: str) -> List[str]:
        # Limit the number of concurrent requests using a Semaphore
        async with self.semaphore:
            r = await self.client.get(target_url)

        # Raise an exception in case of status 400+
        r.raise_for_status()

        # Since crawl.find_urls can be slow, we run this in a separate
        # process so we can free the main thread to do other work
        return await self.loop.run_in_executor(
            self.executor, crawl.find_urls, target_url, r.text
        )

    async def recursive_crawl_url(
        self,
        target_url: str,
        *,
        current_url: Optional[str] = None,
        crawled_urls: Set[str] = {*()},  # Empty set, {} is an empty dict
        recursive_count: int = 0,
        # Sadly there is no good way to define a truly recursive Dict type
        # https://github.com/python/mypy/issues/731
    ) -> Dict[str, Dict]:
        if not current_url:
            current_url = target_url
            crawled_urls.add(target_url)

        found_urls = await self.crawl_url(current_url)
        logging.debug(f"Founded URLs while crawling {current_url}: {found_urls}")
        # Add the found URLs to a result dict, that may be update later after
        # crawling the result recursively
        result = {
            current_url: {
                url: crawl.url_status(url, target_url, crawled_urls)
                for url in found_urls
            }
        }

        if recursive_count >= self.depth_limit:
            logging.debug(
                "Maximum recursive count reached "
                f"({recursive_count}), not crawling further..."
            )
            return result

        urls_to_crawl = crawl.urls_to_crawl(target_url, found_urls, crawled_urls)
        logging.debug(f"Crawling the following URLs recursively: {urls_to_crawl}")
        tasks = [
            self.recursive_crawl_url(
                target_url,
                current_url=url,
                crawled_urls=crawled_urls.union(urls_to_crawl),
                recursive_count=recursive_count + 1,
            )
            for url in urls_to_crawl
        ]

        recursively_found_urls = await asyncio.gather(*tasks, return_exceptions=True)
        # Add the URLs found recursively to the result dict. This may overwritten
        # the previous values from crawl.url_status()
        for found_url_result in recursively_found_urls:
            if isinstance(found_url_result, httpx.HTTPError):
                url = str(found_url_result.request.url)
                result[current_url].update({url: found_url_result})
            else:
                result[current_url].update(found_url_result)

        return result
