import logging
from urllib.parse import urlparse

from src.parsers.base import SiteParser

logger = logging.getLogger(__name__)

_DOMAIN_REGISTRY: dict[str, type[SiteParser]] = {}


def register_parser(domains: list[str], parser_class: type[SiteParser]) -> None:
    for domain in domains:
        _DOMAIN_REGISTRY[domain.lower()] = parser_class


def get_parser(url: str) -> SiteParser:
    domain = urlparse(url).netloc.lower().removeprefix("www.")

    if domain in _DOMAIN_REGISTRY:
        parser = _DOMAIN_REGISTRY[domain]()
        logger.debug("Using %s for %s", type(parser).__name__, domain)
        return parser

    for pattern, parser_cls in _DOMAIN_REGISTRY.items():
        if pattern in domain:
            parser = parser_cls()
            logger.debug(
                "Using %s for %s (matched %s)",
                type(parser).__name__,
                domain,
                pattern,
            )
            return parser

    from src.parsers.generic import GenericParser

    logger.debug("No specific parser for %s, using GenericParser", domain)
    return GenericParser()


def _register_builtins() -> None:
    from src.parsers.amazon import AmazonParser
    from src.parsers.hmt import HMTParser
    from src.parsers.shopify import ShopifyParser

    register_parser(
        ["amazon.in", "amazon.com", "amazon.co.uk", "amazon.de"], AmazonParser
    )
    register_parser(["hmtwatches.store"], HMTParser)
    register_parser(["delhiwatchcompany.com"], ShopifyParser)


_register_builtins()
