"""ElasticSearch e-commerce client package."""

from .clients.sync_client import EcommerceElasticClient
from .clients.async_client import AsyncEcommerceClient
from .models.query_builders import MatchQuery, MatchPhraseQuery, RangeQuery, TermQuery
from .utils.product_generator import generate_product_data, format_product_details

__all__ = [
    'EcommerceElasticClient',
    'AsyncEcommerceClient',
    'MatchQuery',
    'MatchPhraseQuery',
    'RangeQuery',
    'TermQuery',
    'generate_product_data',
    'format_product_details'
] 