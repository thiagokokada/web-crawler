# Web Crawler

Toy URL web crawler done for a take-home assignment.

## Installation

You need to have Python 3.8+ and [poetry](https://python-poetry.org/) installed.
Afterwards run:

```shellsession
$ poetry install
```

To test if the installation worked, you can use:

```shellsession
$ poetry run web-crawler -h
usage: Web Crawler [-h] -u URL [-d DEPTH] [-w WORKERS] [-j] [--debug] [--version]

A simple Python web crawler

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     URL to crawl
  -d DEPTH, --depth DEPTH
                        depth limit (default: 2)
  -w WORKERS, --workers WORKERS
                        maximum number of workers (default: 10)
  -j, --json            output JSON instead of Python's internal representation
  --debug               enable debug log (WARNING: very verbose)
  --version             show program's version number and exit
```

To run the tests:

```shellsession
$ poetry run pytest -vv
```

You can also run [black](https://black.readthedocs.io/en/stable/) to check for
code formatting and [mypy](https://mypy.readthedocs.io) to check for types:

```shellsession
$ poetry run pytest --black --mypy --mypy-ignore-missing-imports
```

There is also a `Makefile` available describing some common commands.

Another option to install is to use the provided `Dockerfile`:

``` shellsession
$ docker build -t web-crawler .
$ docker run -it --rm web-crawler pytest -vv
$ docker run -it --rm web-crawler web-crawler --help
```

## Usage

Crawling a page (the protocol is **required**!):

```shellsession
$ poetry run web-crawler -u 'https://google.com'
```

By default this will recursively crawl the page until hitting the limit of 2.
You can increase this limit by using `-d` parameter:

```shellsession
$ poetry run web-crawler -u 'https://google.com' -d 4
```

To not overload the server with requests, the maximum number of simultaneous
connections is limited. By default up to 10 workers will work concurrently, if
you want to change this limit use the `-w` parameter:

```shellsession
$ poetry run web-crawler -u 'https://google.com' -w 20
```

If you want to output using JSON representation instead of Python's internal
one, you can pass the `-j` flag to it:

```shellsession
$ poetry run web-crawler -u 'https://google.com' -j
```

**Tip:** You can filter the JSON output using `jq`:

```shellsession
$ poetry run web-crawler -u 'https://google.com' -j | jq '."https://google.com"."https://google.com/services"'
```

If you want to debug the application there is also a debug log (**warning:**
very verbose):

```shellsession
$ poetry run web-crawler -u 'https://google.com' -j --debug
```

## Architecture

See [Architecture.md](Architecture.md) file.
