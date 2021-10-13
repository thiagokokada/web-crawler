# Architecture

This document describes the high-level architecture used in this project, and
also explain some of the technical decisions about the dependencies, technology
usage, etc.

## Dependencies

First, I decided to use Python for this project since it is one of the languages
that I have most familiarity, including its ecosystem.

During runtime this project has only 2 direct dependencies:
[BeautifulSoup4](https://beautiful-soup-4.readthedocs.io/) and
[httpx](https://www.python-httpx.org/).

BeautifulSoup4 was chosen since it is the most popular Python library to parse
and scrapping data from HTML files, so it seemed a good fit for this project.

The choose of httpx was a later one when I needed to speed-up the crawler. I
first started this crawler using [requests](https://2.python-requests.org/), a
very popular library to do HTTP requests in Python. However, the first version
of the crawler was slow, mainly because it only did one request at a time. To
enable concurrent requests
[asyncio](https://docs.python.org/3/library/asyncio.html) seemed an interesting
choice (more about why asyncio later), and httpx had an API that was mostly
similar to requests, so I decided to replace requests with httpx.

I decided to use [poetry](https://python-poetry.org/) for dependency management
since poetry fill some gaps compared to more common tools like pip, including
support for lockfiles and automatic management of virtual environments. Also,
since [PEP518](https://www.python.org/dev/peps/pep-0518/) is finally supported
by pip, this project can also be installed using it (e.g.: `pip install .`),
however without support for development dependencies.

Finally, for the development dependencies, I decided to use
[pytest](https://pytest.org/) since it is one of the most popular testing
frameworks in Python, including some plugins to make it working with asyncio,
fixtures and mocking httpx requests easier. This crawler is fully type
annotated, and [mypy](https://mypy.readthedocs.io/) is used to ensure that the
types are making sense (and also avoiding some bugs). To improve the code
consistency, [black](https://black.readthedocs.io/) is used to automatically
format the code.

## High-level architecture

I tried to separate the concerns as much as possible without making the
architecture too complex. The main entrypoint of this crawler is in
`web_crawlers.controllers` namespace, specially in the
`web_crawlers.controllers.Crawler` class. This class is responsible for all the
HTML crawling, including doing requests, parsing HTML and filtering accordingly
to the defined rules. The main method of this class is
`web_crawlers.controllers.Crawler.recursive_crawl_url`, that is responsible for
recursively crawling the target URL and returns the following data structure:

```python
{
    "https://example.com/": {
        "https://google.com": status.DifferentHost(),
        "https://example.com/": status.AlreadyCrawled(),
        "https://example.com/about": {
            "https://google.com": status.DifferentHost(),
            "https://example.com/": status.AlreadyCrawled(),
            "https://example.com/blog": status.AlreadyCrawled(),
            "https://example.com/404": httpx.HttpStatusError(404),
        },
        "https://example.com/blog": {
            "https://google.com": status.DifferentHost(),
        },
    },
}
```

This approach of returning a data structure allows us to easily implement
multiple ways to format the output. For example, the program already implements
two: either a pretty print of a Python's data structure or JSON (using `-j`
flag), but it would be simple to implement other outputing formats. The
trade-off is that we can only print the result after the whole crawling
finishes.

So, for each URL that is found during crawling, it will return a dict with the
crawled URL as a key and either a dict with the crawled URLs or a status/error
of why the crawler didn't go further. The possible status are:

- `AlreadyCrawled()`: this URL was already crawled by some parent URL so it will
  not be crawled again
- `DifferentHost()`: this URL is in a different host, and, accordingly to the
  assignment rules it shouldn't be crawled further
- `InvalidProcotol()`: this URL is not `http://` or `https://`, so no further
  crawling will occur
- `DepthLimit()`: we hit the limit of the recursive crawling count so we will
  not crawl this URL further. The limit is defined by
  `web_crawlers.controllers.Crawler(depth_limit=)` parameter.

To speed-up the crawling we use asyncio, Python's implementation of cooperative
multitasking. Since I am using asyncio this means that there is no true
parallelism occurring here, just concurrency during the `await` calls. However,
since the slowest part of this program is in the HTTP requests, that is I/O
bounded instead of CPU bounded, it seemed that asyncio would solve the problem
well. Python already had good libraries to do async http requests (httpx), so
this seemed to be a good solution for this problem. And it did it, for example
crawling the <https://www.google.com> with 1 workers (effectively without any
concurrency) vs 10 (the default) results in a ~5.6x improvement in total
runtime:

- `poetry run web-crawler -u https://www.google.com -d 2 -w 1 -j  3.15s user 0.15s system 10% cpu 32.912 total`
- `poetry run web-crawler -u https://www.google.com -d 2 -w 10 -j  3.37s user 0.19s system 60% cpu 5.848 total`

About the workers (`-w` parameter) part: this was implemented to avoid
overloading the server with requests. Since this is a recursive crawler, this
could easily make hundreds of simultaneous requests if there was no limit. The
implemention is simple: just a
[semaphore](https://en.wikipedia.org/wiki/Semaphore_(programming)) where the
initial value is equals the number of simultaneous workers. This effectively
allows only to a maximum of n workers actually do a request, while the other
workers need to wait until another worker finishes its job.

One trade-off of using asyncio is that if there is one worker that takes a long
time to process the HTML (that is CPU bounded), this can make all other workers
to wait until this HTML page is processed. To solve this issue we run the HTML
parsing part in a separate process pool with
[ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor).
We can't use `ThreadPoolExecutor` since Python has
[GIL](https://realpython.com/python-gil/), so using it wouldn't make any
difference (or could even make the performance worse).

When possible, I extract most of the logic from the controllers to
`web_crawler.logic.crawl` namespace. This namespace contains only pure
functions, making them trivial to test and run them in parallel (this is why it
is safe to run `web_crawler.logic.crawl.find_urls` in a `ProcessPoolExecutor`).
It also makes changing the behavior of the crawler much easier.

For example, nowadays the crawler only scrapes `<a href="" />` tags. But we can
easily change `web_crawler.logic.crawl.find_urls` function to crawl other types
of URLs, unit testing it to ensure that it is working as it should, and we will
probably don't need to change anything elsewhere.
