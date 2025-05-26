"""Synchronous ElasticSearch client for e-commerce operations."""

import requests
import json
from datetime import datetime
from elasticsearch.clients.base_client import BaseElasticClient
from elasticsearch.models.query_builders import MatchQuery, MatchPhraseQuery, RangeQuery, TermQuery
from elasticsearch.utils.product_generator import format_product_details

class EcommerceElasticClient(BaseElasticClient):
    """Synchronous client for e-commerce operations."""
    
    def __init__(self, host='localhost', port=9200):
        """Initialize the ElasticSearch client for e-commerce operations.
        
        Args:
            host (str): ElasticSearch host (default: localhost)
            port (int): ElasticSearch port (default: 9200)
        """
        super().__init__(host, port)
        self.check_connection()

    def check_connection(self):
        """Check if ElasticSearch is available and log the connection status."""
        try:
            response = requests.get(self.base_url, headers=self.headers)

            if response.status_code == 200:
                version = response.json()['version']['number']
                print(f"Connected successfully to version {version}")
                return True
            else:
                print(f"Failed to connect to ElasticSearch: {response.text}")
                return False
        except Exception as e:
            print(f"Error connecting to ElasticSearch: {str(e)}")
            return False

    def create_index(self, index_name, mappings=None):
        """Create an ElasticSearch index with optional mappings.
        
        Args:
            index_name (str): Name of the index to create
            mappings (dict, optional): Index mappings/schema definition
        """
        url = f"{self.base_url}/{index_name}"
        response = requests.head(url, headers=self.headers)
        if response.status_code == 200:
            print(f"Index {index_name} already exists")
            return True

        body = {}
        if mappings:
            body["mappings"] = mappings

        response = requests.put(url, headers=self.headers, data=json.dumps(body) if body else None)

        if response.status_code in (200, 201):
            print(f"Created index {index_name}")
            return True
        else:
            print(f"Failed to create index {index_name}: {response.text}")
            return False

    def create_product_index(self):
        """Create the main products index with proper mappings."""
        index_name = "ecommerce_products"
        mappings = {
            "properties": {
                "ID": {"type": "integer"},
                "Name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "Description": {"type": "text"},
                "Category": {"type": "keyword"},
                "Subcategory": {"type": "keyword"},
                "Price": {"type": "float"},
                "StockQty": {"type": "integer"},
                "Brand": {"type": "keyword"},
                "CreatedTime": {"type": "date"},
                "UpdatedTime": {"type": "date"},
                "Rating": {
                    "type": "float",
                    "minimum": 0,
                    "maximum": 5
                },
                "Active": {"type": "boolean"}
            }
        }
        
        return self.create_index(index_name, mappings)

    def index_document(self, index_name, document, doc_id=None):
        """Index a document in ElasticSearch.
        
        Args:
            index_name (str): Target index name
            document (dict): Document to index
            doc_id (str, optional): Custom document ID
        """
        if doc_id:
            url = f"{self.base_url}/{index_name}/_doc/{doc_id}"
        else:
            url = f"{self.base_url}/{index_name}/_doc"

        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(document))
            
            if response.status_code in (200, 201):
                result = response.json()
                print(f"Document indexed successfully with ID: {result['_id']}")
                return result
            else:
                print(f"Failed to index document: {response.text}")
                return None
        except Exception as e:
            print(f"Error indexing document: {str(e)}")
            return None

    def create_product(self, product_data):
        """Create a single product.
        
        Args:
            product_data (dict): Product data including all required fields
            
        Returns:
            dict: Response from ElasticSearch with created document details
        """
        index_name = "ecommerce_products"
        
        # Validate required fields
        required_fields = ["Name", "Description", "Category", "Price", "StockQty", "Brand"]
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Add timestamps if not provided
        if "CreatedTime" not in product_data:
            product_data["CreatedTime"] = datetime.now().isoformat()
        if "UpdatedTime" not in product_data:
            product_data["UpdatedTime"] = datetime.now().isoformat()
        
        return self.index_document(index_name, product_data)

    def get_product_by_id(self, product_id):
        """Retrieve a product by its ID.
        
        Args:
            product_id (str): The ID of the product to retrieve
            
        Returns:
            dict: Product document if found, None otherwise
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_doc/{product_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return result["_source"]
            elif response.status_code == 404:
                print(f"Product with ID {product_id} not found")
                return None
            else:
                print(f"Error retrieving product: {response.text}")
                return None
        except Exception as e:
            print(f"Error getting product: {str(e)}")
            return None

    def update_product(self, product_id, update_data):
        """Update specific fields of a product.
        
        Args:
            product_id (str): ID of the product to update
            update_data (dict): Fields to update with new values
            
        Returns:
            dict: Updated product document if successful, None otherwise
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_update/{product_id}"
        
        # Add update timestamp
        update_data["UpdatedTime"] = datetime.now().isoformat()
        
        # Prepare update script
        update_body = {
            "doc": update_data,
            "doc_as_upsert": True
        }
        
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(update_body))
            
            if response.status_code in (200, 201):
                result = response.json()
                print(f"Successfully updated product {product_id}")
                return result
            else:
                print(f"Failed to update product: {response.text}")
                return None
        except Exception as e:
            print(f"Error updating product: {str(e)}")
            return None

    def delete_product(self, product_id, soft_delete=True):
        """Delete a product (soft or hard delete).
        
        Args:
            product_id (str): ID of the product to delete
            soft_delete (bool): If True, marks as inactive instead of deleting
            
        Returns:
            bool: True if successful, False otherwise
        """
        if soft_delete:
            # Soft delete by updating Active status
            return self.update_product(product_id, {"Active": False}) is not None
        else:
            # Hard delete
            index_name = "ecommerce_products"
            url = f"{self.base_url}/{index_name}/_doc/{product_id}"
            
            try:
                response = requests.delete(url, headers=self.headers)
                
                if response.status_code == 200:
                    print(f"Successfully deleted product {product_id}")
                    return True
                else:
                    print(f"Failed to delete product: {response.text}")
                    return False
            except Exception as e:
                print(f"Error deleting product: {str(e)}")
                return False

    def search_products_by_name(self, product_name, fuzzy=False):
        """Search products by name with optional fuzzy matching.
        
        Args:
            product_name (str): Name to search for
            fuzzy (bool): If True, enables fuzzy matching
            
        Returns:
            list: List of matching products
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        # Create appropriate query based on fuzzy parameter
        if fuzzy:
            query = {
                "match": {
                    "Name": {
                        "query": product_name,
                        "fuzziness": "AUTO"
                    }
                }
            }
        else:
            query = {
                "match_phrase": {
                    "Name": {
                        "query": product_name
                    }
                }
            }
        
        # Wrap in search query
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products matching '{product_name}':")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_price_range(self, min_price, max_price):
        """Find products within a price range.
        
        Args:
            min_price (float): Minimum price
            max_price (float): Maximum price
            
        Returns:
            list: List of products within the price range
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        # Create range query
        query = {
            "range": {
                "Price": {
                    "gte": min_price,
                    "lte": max_price
                }
            }
        }
        
        # Wrap in search query
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products in price range ${min_price} - ${max_price}:")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_category(self, category):
        """Search products by category.
        
        Args:
            category (str): Category to search for
            
        Returns:
            list: List of products in the category
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        query = {
            "term": {
                "Category": category
            }
        }
        
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products in category '{category}':")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_brand(self, brand):
        """Search products by brand.
        
        Args:
            brand (str): Brand to search for
            
        Returns:
            list: List of products from the brand
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        query = {
            "term": {
                "Brand": brand
            }
        }
        
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products from brand '{brand}':")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_rating(self, min_rating):
        """Search products by minimum rating.
        
        Args:
            min_rating (float): Minimum rating to search for
            
        Returns:
            list: List of products with rating >= min_rating
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        query = {
            "range": {
                "Rating": {
                    "gte": min_rating
                }
            }
        }
        
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products with rating >= {min_rating}:")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_stock(self, min_stock):
        """Search products by minimum stock quantity.
        
        Args:
            min_stock (int): Minimum stock quantity to search for
            
        Returns:
            list: List of products with stock >= min_stock
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        query = {
            "range": {
                "StockQty": {
                    "gte": min_stock
                }
            }
        }
        
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products with stock >= {min_stock}:")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_by_date_range(self, start_date, end_date):
        """Search products by creation date range.
        
        Args:
            start_date (str): Start date in ISO format
            end_date (str): End date in ISO format
            
        Returns:
            list: List of products created within the date range
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        query = {
            "range": {
                "CreatedTime": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
        
        search_query = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                products = [hit["_source"] for hit in hits]
                
                # Display formatted results
                print(f"\nFound {len(products)} products created between {start_date} and {end_date}:")
                for product in products:
                    print("\n" + "="*50)
                    print(format_product_details(product))
                
                return products
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def search_products(self, query_builder):
        """Generic search method that accepts a query builder.
        
        Args:
            query_builder: An object that implements to_dict() method for query construction
            
        Returns:
            list: List of matching products
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_search"
        
        # Build search query
        search_query = {"query": query_builder.to_dict()}
        
        try:
            response = requests.get(url, headers=self.headers, data=json.dumps(search_query))
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                return [hit["_source"] for hit in hits]
            else:
                print(f"Search failed: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching products: {str(e)}")
            return []

    def bulk_create_products(self, products_list):
        """Create multiple products in a single bulk operation.
        
        Args:
            products_list (list): List of product documents to create
            
        Returns:
            dict: Bulk operation response
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
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/x-ndjson"},
                data=bulk_body
            )
            
            if response.status_code == 200:
                print(f"Successfully bulk created {len(products_list)} products")
                return response.json()
            else:
                print(f"Bulk creation failed: {response.text}")
                return None
        except Exception as e:
            print(f"Error in bulk creation: {str(e)}")
            return None

    def bulk_update_prices(self, price_adjustments):
        """Update prices for multiple products.
        
        Args:
            price_adjustments (list): List of dicts with product_id and new_price
            
        Returns:
            dict: Bulk operation response
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
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/x-ndjson"},
                data=bulk_body
            )
            
            if response.status_code == 200:
                print(f"Successfully updated prices for {len(price_adjustments)} products")
                return response.json()
            else:
                print(f"Bulk price update failed: {response.text}")
                return None
        except Exception as e:
            print(f"Error in bulk price update: {str(e)}")
            return None

    def bulk_delete_products(self, product_ids, soft_delete=True):
        """Delete multiple products.
        
        Args:
            product_ids (list): List of product IDs to delete
            soft_delete (bool): If True, marks as inactive instead of deleting
            
        Returns:
            dict: Bulk operation response
        """
        if soft_delete:
            # Prepare bulk update for soft delete
            updates = [{"product_id": pid, "new_price": None} for pid in product_ids]
            return self.bulk_update_prices(updates)
        else:
            index_name = "ecommerce_products"
            url = f"{self.base_url}/_bulk"
            
            # Prepare bulk request body
            bulk_body = ""
            for product_id in product_ids:
                action = {
                    "delete": {
                        "_index": index_name,
                        "_id": product_id
                    }
                }
                bulk_body += json.dumps(action) + "\n"
            
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/x-ndjson"},
                    data=bulk_body
                )
                
                if response.status_code == 200:
                    print(f"Successfully deleted {len(product_ids)} products")
                    return response.json()
                else:
                    print(f"Bulk deletion failed: {response.text}")
                    return None
            except Exception as e:
                print(f"Error in bulk deletion: {str(e)}")
                return None 