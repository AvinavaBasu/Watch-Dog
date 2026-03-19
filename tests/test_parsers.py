import pytest
from bs4 import BeautifulSoup
from src.parsers import get_parser
from src.parsers.amazon import AmazonParser
from src.parsers.hmt import HMTParser
from src.parsers.shopify import ShopifyParser
from src.parsers.generic import GenericParser


class TestParserRegistry:
    def test_amazon_in_detected(self):
        parser = get_parser("https://www.amazon.in/dp/B0DRQSHJSC/")
        assert isinstance(parser, AmazonParser)

    def test_amazon_com_detected(self):
        parser = get_parser("https://www.amazon.com/dp/B0DRQSHJSC/")
        assert isinstance(parser, AmazonParser)

    def test_hmt_detected(self):
        parser = get_parser("https://www.hmtwatches.store/product/some-id")
        assert isinstance(parser, HMTParser)

    def test_shopify_dwc_detected(self):
        parser = get_parser("https://delhiwatchcompany.com/products/dwc-terra")
        assert isinstance(parser, ShopifyParser)

    def test_unknown_site_uses_generic(self):
        parser = get_parser("https://www.unknown-shop.com/product/123")
        assert isinstance(parser, GenericParser)


class TestHMTParser:
    def test_out_of_stock(self):
        html = '<html><body><h1>HMT Watch</h1><span>Out of Stock</span></body></html>'
        parser = HMTParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is False

    def test_in_stock(self):
        html = '<html><body><h1>HMT Watch</h1><button>Add to Cart</button></body></html>'
        parser = HMTParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is True

    def test_extract_price(self):
        html = '<html><body><h1>HMT Watch</h1><div>₹7275</div></body></html>'
        parser = HMTParser()
        soup = BeautifulSoup(html, "html.parser")
        price = parser.extract_price(soup)
        assert price is not None
        assert "7275" in price


class TestShopifyParser:
    def test_sold_out(self):
        html = '<html><body><h1>DWC Terra</h1><button disabled>Sold Out</button></body></html>'
        parser = ShopifyParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is False

    def test_add_to_cart(self):
        html = '<html><body><h1>DWC Terra</h1><button>Add to cart</button></body></html>'
        parser = ShopifyParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is True

    def test_extract_price(self):
        html = '<html><body><span class="price-item--regular">Rs. 3,999.00</span></body></html>'
        parser = ShopifyParser()
        soup = BeautifulSoup(html, "html.parser")
        price = parser.extract_price(soup)
        assert price is not None
        assert "3,999" in price


class TestGenericParser:
    def test_generic_out_of_stock(self):
        html = '<html><body><h1>Some Product</h1><p>This product is out of stock</p></body></html>'
        parser = GenericParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is False

    def test_generic_add_to_cart(self):
        html = '<html><body><h1>Some Product</h1><button>Add to Cart</button></body></html>'
        parser = GenericParser()
        soup = BeautifulSoup(html, "html.parser")
        assert parser.detect_availability(soup, html) is True
