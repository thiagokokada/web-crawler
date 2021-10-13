# TODO

- [x] To have a correctly recursive crawler (one that can crawl its sub-domains,
  its sub-sub-domains, etc, without repeating them), we can have the following 
  strategy:

  1. For each URL that we found and it have the same base URL as the current
  URL, add it to a list/set. For example:

      ```python
      # Found "https://example.com/blog" and "https://something.com"
      # in "https://example.com":
      crawlers = ["https://example.com", "https://example.com/blog"]
      ```

  2. Only start a new crawler if current URL is not in `crawlers` list and
  `web_crawler.logic.crawl.same_base_url()` is `True`

  `crawlers` will have concurrent access. So we need some way to control this.
  And take care about not doing granular updates (i.e.: to avoid locking too 
  much), maybe update the whole list/set with all URLs that match the
  condition.

- [x] Take care of infinite loops. Probably a recursion count limit will be good.
- [x] Change representation for something that makes the represents the hierarchy
  of the crawler better. For example:

  ```python
  {
      "https://example.com": {
          "https://example.com/about": "No more URLs",
          "https://example.com/blog": {
              "https://example.com/blog/1": "No more URLs",
          },
          "https://google.com": "Different host",
      },
  }
  ```
- [x] Improve `web_crawler.logic.crawl.find_urls()` function to ignore some URLs
  variations (like `https://google.com/foo` and `https://google.com/foo#bar` 
  should be considered the same)
- [x] Treat `https://example.com` and `https://example.com/` as the same URL
- [x] Treat asynchronous errors in `web_crawler.controllers.Crawler.crawl_url()`

