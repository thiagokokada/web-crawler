from pathlib import Path

import pytest

from web_crawler.logic import crawl
from web_crawler.models import status


def test_same_host():
    # Trivial case
    assert crawl.same_host("https://example.com", "https://example.com")
    # Returns True when the host match
    assert crawl.same_host("https://example.com", "https://example.com/blog")
    assert crawl.same_host(
        "https://example.com/blog", "https://example.com/blog/article"
    )
    # Returns False in empty case
    assert not crawl.same_host("http://example.com", "")
    # Base URL should comes first
    assert not crawl.same_host("https://example.com/blog", "https://example.com")
    # Returns False when the protocol is different
    assert not crawl.same_host("http://example.com", "https://example.com/blog")
    # Returns False when the host doesn't match
    assert not crawl.same_host("https://example.com", "https://google.com/reader")


def test_filter_url():
    # Trivial case
    assert crawl.filter_url("https://example.com") == "https://example.com"
    # Remove trailing /
    assert crawl.filter_url("https://example.com/") == "https://example.com"
    # Preserve paths
    assert crawl.filter_url("https://example.com/abc") == "https://example.com/abc"
    # Preserve paths, remove trailing /
    assert crawl.filter_url("https://example.com/abc/") == "https://example.com/abc"
    # Remove #
    assert crawl.filter_url("https://example.com#") == "https://example.com"
    # Remove query strings
    assert (
        crawl.filter_url("https://example.com/abc?query") == "https://example.com/abc"
    )
    # Remove both
    assert (
        crawl.filter_url("https://example.com/abc#cba?query")
        == "https://example.com/abc"
    )


def test_get_url():
    # Works in empty case
    assert crawl.get_url("https://example.com", "") == "https://example.com"
    # Works in root path
    assert crawl.get_url("https://example.com", "/") == "https://example.com"
    # Works with valid paths
    assert crawl.get_url("https://example.com", "abc") == "https://example.com/abc"
    assert crawl.get_url("https://example.com", "/blog") == "https://example.com/blog"
    assert crawl.get_url("http://example.com", "/blog") == "http://example.com/blog"
    # Works with full URL (and returns the URL itself)
    assert (
        crawl.get_url("https://example.com", "https://www.google.com")
        == "https://www.google.com"
    )


def test_find_urls(datafix_read, datafix_readbin):
    # Empty case
    assert crawl.find_urls("https://emptypage.com", "") == []
    # Return empty with plain text
    assert crawl.find_urls("https://plaintext.com", "Hello World!") == []
    # Return empty with binaries
    assert crawl.find_urls("https://binarytext.com", b"") == []
    assert (
        crawl.find_urls("https://nonhtml.com/image.png", datafix_readbin("image.png"))
        == []
    )
    # Should crawl correctly all links in a page
    assert crawl.find_urls(
        "https://choosealicense.com", datafix_read("choosealicense.html")
    ) == [
        "https://choosealicense.com/community",
        "https://choosealicense.com/no-permission",
        "https://choosealicense.com/licenses/mit",
        "https://github.com/babel/babel/blob/master/LICENSE",
        "https://github.com/dotnet/runtime/blob/master/LICENSE.TXT",
        "https://github.com/rails/rails/blob/master/MIT-LICENSE",
        "https://choosealicense.com/licenses/gpl-3.0",
        "https://github.com/ansible/ansible/blob/devel/COPYING",
        "https://git.savannah.gnu.org/cgit/bash.git/tree/COPYING",
        "https://git.gnome.org/browse/gimp/tree/COPYING",
        "https://choosealicense.com/non-software",
        "https://choosealicense.com/licenses",
        "https://choosealicense.com/about",
        "https://choosealicense.com/terms-of-service",
        "https://github.com/github/choosealicense.com/edit/gh-pages/index.html",
        "https://creativecommons.org/licenses/by/3.0",
        "https://github.com",
        "https://github.com/github/choosealicense.com",
    ]


def test_urls_to_crawl():
    # Empty case
    assert crawl.urls_to_crawl("https://example.com", [], []) == []
    # Should crawl domains in the same host
    assert crawl.urls_to_crawl(
        "https://example.com", ["https://example.com/about"], []
    ) == ["https://example.com/about"]
    # Shouldn't crawl domains already crawled before
    assert (
        crawl.urls_to_crawl(
            "https://example.com",
            ["https://example.com/about"],
            ["https://example.com/about"],
        )
        == []
    )
    # Shouldn't crawl domains in another host
    assert (
        crawl.urls_to_crawl(
            "https://example.com",
            ["https://community.example.com", "https://google.com"],
            [],
        )
        == []
    )
    # Combining rules
    assert (
        crawl.urls_to_crawl(
            "https://example.com",
            [
                "https://example.com",
                "https://example.com/about",
                "https://example.com/blog",
                "https://community.example.com",
                "https://google.com",
            ],
            [
                "https://example.com",
                "https://example.com/blog",
            ],
        )
        == ["https://example.com/about"]
    )


def test_url_status():
    # Exausted the search
    assert (
        crawl.url_status("https://example.com", "https://example.com", [])
        == status.DepthLimit()
    )
    # Invalid protocol
    assert (
        crawl.url_status("ftp://example.com", "https://example.com", [])
        == status.InvalidProtocol()
    )
    # Current URL is in crawled_urls already
    assert (
        crawl.url_status(
            "https://example.com", "https://example.com", ["https://example.com"]
        )
        == status.AlreadyCrawled()
    )
    # Current URL is in different host (so it will not be crawled further)
    assert (
        crawl.url_status(
            "https://google.com", "https://example.com", ["https://example.com"]
        )
        == status.DifferentHost()
    )
