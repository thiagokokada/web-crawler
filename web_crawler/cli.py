import argparse
import logging
from json import dumps
from pprint import pp
from typing import List, Optional

from web_crawler import __version__
from web_crawler.controllers import web_crawler


async def main(args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        prog="Web Crawler",
        description="A simple Python web crawler",
    )
    parser.add_argument(
        "-u",
        "--url",
        help="URL to crawl",
        default=None,
        required=True,
    )
    parser.add_argument(
        "-d",
        "--depth",
        help="depth limit (default: 2)",
        type=int,
        default=2,
        required=False,
    )
    parser.add_argument(
        "-w",
        "--workers",
        help="maximum number of workers (default: 10)",
        type=int,
        default=10,
        required=False,
    )
    parser.add_argument(
        "-j",
        "--json",
        help="output JSON instead of Python's internal representation",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--debug",
        help="enable debug log (WARNING: very verbose)",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parsed_args = parser.parse_args(args=args)

    if parsed_args.debug:
        logging.root.setLevel(logging.DEBUG)

    depth = parsed_args.depth
    workers = parsed_args.workers
    json = parsed_args.json

    crawler = web_crawler.Crawler(depth, workers)

    if url := parsed_args.url:
        result = await crawler.recursive_crawl_url(url)
        if json:
            print(dumps(result, default=repr, indent=2))
        else:
            pp(result)
