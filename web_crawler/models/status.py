from abc import ABC
from dataclasses import dataclass


class WebCrawlerStatus(ABC):
    pass


@dataclass
class AlreadyCrawled(WebCrawlerStatus):
    pass


@dataclass
class InvalidProtocol(WebCrawlerStatus):
    pass


@dataclass
class DifferentHost(WebCrawlerStatus):
    pass


@dataclass
class DepthLimit(WebCrawlerStatus):
    pass
