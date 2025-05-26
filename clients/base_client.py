"""Base ElasticSearch client class."""

import requests
import json
from datetime import datetime
from elasticsearch.models.query_builders import MatchQuery, MatchPhraseQuery, RangeQuery, TermQuery
from ..utils.product_generator import format_product_details

class BaseElasticClient:
    """Base class for ElasticSearch clients."""
    
    def __init__(self, host='localhost', port=9200):
        """Initialize the ElasticSearch client.
        
        Args:
            host (str): ElasticSearch host (default: localhost)
            port (int): ElasticSearch port (default: 9200)
        """
        self.base_url = f"http://{host}:{port}"
        self.headers = {"Content-Type": "application/json"}
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
        """Create the main products index with proper mappings.
        
        Returns:
            bool: True if index was created successfully, False otherwise
        """
        index_name = "ecommerce_products"
        mappings = {
            "properties": {
                "ID": {"type": "integer"},
                "Name": {
                    "type": "text",    # For full-text search
                    "fields": {
                        "keyword": {    # Sub-field for exact matching
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

    def delete_product_index(self):
        """Delete the products index (use with caution).
        
        Returns:
            bool: True if index was deleted successfully, False otherwise
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            
            if response.status_code == 200:
                print(f"Successfully deleted index {index_name}")
                return True
            elif response.status_code == 404:
                print(f"Index {index_name} does not exist")
                return False
            else:
                print(f"Failed to delete index {index_name}: {response.text}")
                return False
        except Exception as e:
            print(f"Error deleting index {index_name}: {str(e)}")
            return False

    def check_index_health(self):
        """Check the health and status of the products index.
        
        Returns:
            dict: Dictionary containing index health information
        """
        index_name = "ecommerce_products"
        url = f"{self.base_url}/{index_name}/_stats"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                stats = response.json()
                index_stats = stats['indices'][index_name]
                
                health_url = f"{self.base_url}/_cluster/health/{index_name}"
                health_response = requests.get(health_url, headers=self.headers)
                health_info = health_response.json() if health_response.status_code == 200 else {}
                
                health_data = {
                    "status": health_info.get("status", "unknown"),
                    "number_of_shards": health_info.get("number_of_shards", 0),
                    "number_of_replicas": health_info.get("number_of_replicas", 0),
                    "active_shards": health_info.get("active_shards", 0),
                    "unassigned_shards": health_info.get("unassigned_shards", 0),
                    "document_count": index_stats.get("total", {}).get("docs", {}).get("count", 0)
                }
                
                print(f"Index health check results for {index_name}:")
                print(json.dumps(health_data, indent=2))
                return health_data
            else:
                print(f"Failed to get index stats: {response.text}")
                return None
        except Exception as e:
            print(f"Error checking index health: {str(e)}")
            return None 