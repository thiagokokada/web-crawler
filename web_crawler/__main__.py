import asyncio

from web_crawler import cli


def run():
    asyncio.run(cli.main())


if __name__ == "__main__":
    run()
