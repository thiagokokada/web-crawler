import pytest
import httpx

from web_crawler.controllers import web_crawler
from web_crawler.models import status


@pytest.mark.asyncio
async def test_crawl_url(datafix_read, httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com",
        data=datafix_read("example.html"),
    )

    crawler = web_crawler.Crawler()
    result = await crawler.crawl_url("https://example.com")

    assert result == [
        "https://google.com",
        "https://example.com",
        "https://example.com/about",
        "https://example.com/blog",
    ]


@pytest.mark.asyncio
async def test_recursive_crawl_url(datafix_read, httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com",
        data=datafix_read("example.html"),
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/about",
        data=datafix_read("about.html"),
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/blog",
        data=datafix_read("blog.html"),
    )
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/blog/1",
        data=datafix_read("blog_1.html"),
    )

    crawler = web_crawler.Crawler()
    result = await crawler.recursive_crawl_url("https://example.com")

    assert result == {
        "https://example.com": {
            "https://google.com": status.DifferentHost(),
            "https://example.com": status.AlreadyCrawled(),
            "https://example.com/about": {
                "https://google.com": status.DifferentHost(),
                "https://example.com": status.AlreadyCrawled(),
                "https://example.com/blog": status.AlreadyCrawled(),
                "mailto://someone@example.com": status.InvalidProtocol(),
            },
            "https://example.com/blog": {
                "https://example.com/blog/1": {},
                "https://google.com": status.DifferentHost(),
            },
        },
    }

    # Testing depth_limit
    crawler = web_crawler.Crawler(depth_limit=0)
    result = await crawler.recursive_crawl_url("https://example.com")

    assert result == {
        "https://example.com": {
            "https://google.com": status.DifferentHost(),
            "https://example.com": status.AlreadyCrawled(),
            "https://example.com/about": status.DepthLimit(),
            "https://example.com/blog": status.DepthLimit(),
        },
    }


@pytest.mark.asyncio
async def test_recursive_crawl_url_error_handling(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://httpstatuses.com",
        data=b"""
        <a href='/home'>Home</a>
        <a href='/404'>404</a>
        <a href='/500'>500</a>
        """,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://httpstatuses.com/home",
    )
    httpx_mock.add_response(
        method="GET",
        url="https://httpstatuses.com/404",
        status_code=404,
    )
    httpx_mock.add_response(
        method="GET",
        url="https://httpstatuses.com/500",
        status_code=500,
    )

    crawler = web_crawler.Crawler()
    result = await crawler.recursive_crawl_url("https://httpstatuses.com")

    # Making sure that crawling doesn't stop even if we receive an error
    home = result["https://httpstatuses.com"]["https://httpstatuses.com/home"]
    assert home == {}

    error404 = result["https://httpstatuses.com"]["https://httpstatuses.com/404"]
    assert isinstance(error404, httpx.HTTPStatusError)
    assert error404.response.status_code == 404

    error500 = result["https://httpstatuses.com"]["https://httpstatuses.com/500"]
    assert isinstance(error500, httpx.HTTPStatusError)
    assert error500.response.status_code == 500
