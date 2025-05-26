"""Asynchronous ElasticSearch client for e-commerce operations."""

import json
from datetime import datetime
from requests_futures.sessions import FuturesSession
from .base_client import BaseElasticClient
from ..models.query_builders import MatchQuery, MatchPhraseQuery, RangeQuery, TermQuery
from ..utils.product_generator import format_product_details

class AsyncEcommerceClient(BaseElasticClient):
    """Asynchronous client for e-commerce operations using requests-futures."""
    
    def __init__(self, host='localhost', port=9200, max_workers=10):
        """Initialize the async ElasticSearch client.
        
        Args:
            host (str): ElasticSearch host (default: localhost)
            port (int): ElasticSearch port (default: 9200)
            max_workers (int): Maximum number of concurrent workers (default: 10)
        """
        super().__init__(host, port)
        self.session = FuturesSession(max_workers=max_workers)
        self.futures = []

    def async_bulk_index(self, products_list):
        """Asynchronously index multiple products.
        
        Args:
            products_list (list): List of product documents to index
            
        Returns:
            Future: Future object for the bulk operation
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/_bulk"
        
        # Prepare bulk request body
        bulk_body = ""
        for product in products_list:
            # Add timestamps if not present
            if "CreatedTime" not in product:
                product["CreatedTime"] = datetime.now().isoformat()
            if "UpdatedTime" not in product:
                product["UpdatedTime"] = datetime.now().isoformat()
            
            # Add action metadata
            action = {"index": {"_index": index_name}}
            bulk_body += json.dumps(action) + "\n"
            bulk_body += json.dumps(product) + "\n"
        
        # Submit async request
        future = self.session.post(
            url,
            headers={"Content-Type": "application/x-ndjson"},
            data=bulk_body
        )
        self.futures.append(future)
        return future

    def async_multi_search(self, query_builders):
        """Perform multiple searches concurrently.
        
        Args:
            query_builders (list): List of query builder objects
            
        Returns:
            list: List of Future objects for each search
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_msearch"
        
        # Prepare multi-search request body
        search_body = ""
        for query_builder in query_builders:
            # Add index header
            search_body += json.dumps({"index": index_name}) + "\n"
            # Add search query
            search_body += json.dumps({"query": query_builder.to_dict()}) + "\n"
        
        # Submit async request
        future = self.session.post(
            url,
            headers={"Content-Type": "application/x-ndjson"},
            data=search_body
        )
        self.futures.append(future)
        return future

    def async_batch_updates(self, updates_list):
        """Perform multiple update operations concurrently.
        
        Args:
            updates_list (list): List of dicts with product_id and update_data
            
        Returns:
            list: List of Future objects for each update
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/_bulk"
        
        # Prepare bulk request body
        bulk_body = ""
        for update in updates_list:
            product_id = update["product_id"]
            update_data = update["update_data"]
            
            # Add update timestamp
            update_data["UpdatedTime"] = datetime.now().isoformat()
            
            # Create update action
            action = {
                "update": {
                    "_index": index_name,
                    "_id": product_id
                }
            }
            
            # Create update document
            doc = {"doc": update_data}
            
            bulk_body += json.dumps(action) + "\n"
            bulk_body += json.dumps(doc) + "\n"
        
        # Submit async request
        future = self.session.post(
            url,
            headers={"Content-Type": "application/x-ndjson"},
            data=bulk_body
        )
        self.futures.append(future)
        return future

    def wait_for_all_operations(self):
        """Wait for all async operations to complete and return results.
        
        Returns:
            list: List of results from completed operations
        """
        results = []
        for future in self.futures:
            try:
                response = future.result()
                if response.status_code in (200, 201):
                    results.append(response.json())
                else:
                    print(f"Operation failed: {response.text}")
                    results.append(None)
            except Exception as e:
                print(f"Error in async operation: {str(e)}")
                results.append(None)
        
        # Clear futures list
        self.futures = []
        return results

    def async_search_by_criteria(self, criteria_list):
        """Perform multiple searches based on different criteria concurrently.
        
        Args:
            criteria_list (list): List of dicts with search criteria
            
        Returns:
            list: Combined results from all searches
        """
        query_builders = []
        
        for criteria in criteria_list:
            if "name" in criteria:
                if criteria.get("fuzzy", False):
                    query_builders.append(MatchQuery("Name.text", criteria["name"], "AUTO"))
                else:
                    query_builders.append(MatchPhraseQuery("Name.text", criteria["name"]))
            
            elif "price_range" in criteria:
                min_price = criteria["price_range"].get("min")
                max_price = criteria["price_range"].get("max")
                query_builders.append(RangeQuery("Price", gte=min_price, lte=max_price))
            
            elif "category" in criteria:
                query_builders.append(TermQuery("Category", criteria["category"]))
            
            elif "brand" in criteria:
                query_builders.append(TermQuery("Brand", criteria["brand"]))
            
            elif "min_rating" in criteria:
                query_builders.append(RangeQuery("Rating", gte=criteria["min_rating"]))
            
            elif "min_stock" in criteria:
                query_builders.append(RangeQuery("StockQty", gte=criteria["min_stock"]))
        
        # Perform multi-search
        future = self.async_multi_search(query_builders)
        response = future.result()
        
        if response.status_code == 200:
            results = response.json()
            all_products = []
            
            # Process each search result
            for result in results.get("responses", []):
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                all_products.extend(products)
            
            # Remove duplicates based on ID
            unique_products = {p["ID"]: p for p in all_products}.values()
            
            print(f"\nFound {len(unique_products)} unique products matching criteria")
            for product in unique_products:
                print(format_product_details(product))
            
            return list(unique_products)
        else:
            print(f"Multi-search failed: {response.text}")
            return []

    def async_bulk_price_updates(self, price_adjustments):
        """Asynchronously update prices for multiple products.
        
        Args:
            price_adjustments (list): List of dicts with product_id and new_price
            
        Returns:
            Future: Future object for the bulk operation
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/_bulk"
        
        # Prepare bulk request body
        bulk_body = ""
        for adjustment in price_adjustments:
            product_id = adjustment["product_id"]
            new_price = adjustment["new_price"]
            
            # Create update action
            action = {
                "update": {
                    "_index": index_name,
                    "_id": product_id
                }
            }
            
            # Create update document
            doc = {
                "doc": {
                    "Price": new_price,
                    "UpdatedTime": datetime.now().isoformat()
                }
            }
            
            bulk_body += json.dumps(action) + "\n"
            bulk_body += json.dumps(doc) + "\n"
        
        # Submit async request
        future = self.session.post(
            url,
            headers={"Content-Type": "application/x-ndjson"},
            data=bulk_body
        )
        self.futures.append(future)
        return future 