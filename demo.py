"""Demo script to showcase ElasticSearch client functionality."""

import time
from datetime import datetime, timedelta
from elasticsearch.clients.sync_client import EcommerceElasticClient
from elasticsearch.clients.async_client import AsyncEcommerceClient
from elasticsearch.utils.product_generator import generate_product_data

def demo_sync_client():
    """Demonstrate synchronous client operations."""
    print("\n=== Synchronous Client Demo ===")
    
    # Initialize client
    client = EcommerceElasticClient()
    
    # Create index
    print("\nCreating product index...")
    client.create_product_index()
    
    # Generate and index sample products
    print("\nGenerating and indexing sample products...")
    products = generate_product_data(10)  # Generate 10 products for demo
    client.bulk_create_products(products)
    
    # Search operations
    print("\nPerforming search operations...")
    
    # Search by name
    print("\nSearching by name (exact match):")
    client.search_products_by_name("laptop")
    
    print("\nSearching by name (fuzzy match):")
    client.search_products_by_name("laptp", fuzzy=True)
    
    # Search by price range
    print("\nSearching by price range:")
    client.search_by_price_range(100, 500)
    
    # Search by category
    print("\nSearching by category:")
    client.search_by_category("Electronics")
    
    # Search by brand
    print("\nSearching by brand:")
    client.search_by_brand("Apple")
    
    # Search by rating
    print("\nSearching by minimum rating:")
    client.search_by_rating(4.0)
    
    # Search by stock
    print("\nSearching by minimum stock:")
    client.search_by_stock(50)
    
    # Search by date range
    print("\nSearching by date range:")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    client.search_by_date_range(start_date.isoformat(), end_date.isoformat())
    
    # Update operations
    print("\nPerforming update operations...")
    
    # Update single product
    if products:
        product_id = products[0]["ID"]
        print(f"\nUpdating product {product_id}:")
        client.update_product(product_id, {"Price": 999.99})
    
    # Bulk price updates
    print("\nPerforming bulk price updates:")
    price_adjustments = [
        {"product_id": p["ID"], "new_price": p["Price"] * 1.1}  # 10% price increase
        for p in products[:3]
    ]
    client.bulk_update_prices(price_adjustments)
    
    # Delete operations
    print("\nPerforming delete operations...")
    
    # Soft delete
    if products:
        product_id = products[-1]["ID"]
        print(f"\nSoft deleting product {product_id}:")
        client.delete_product(product_id, soft_delete=True)
    
    # Hard delete
    if len(products) > 1:
        product_id = products[-2]["ID"]
        print(f"\nHard deleting product {product_id}:")
        client.delete_product(product_id, soft_delete=False)
    
    # Check index health
    print("\nChecking index health:")
    client.check_index_health()

def demo_async_client():
    """Demonstrate asynchronous client operations."""
    print("\n=== Asynchronous Client Demo ===")
    
    # Initialize client
    client = AsyncEcommerceClient(max_workers=5)
    
    # Create index
    print("\nCreating product index...")
    client.create_product_index()
    
    # Generate and index sample products
    print("\nGenerating and indexing sample products...")
    products = generate_product_data(10)
    future = client.async_bulk_index(products)
    client.wait_for_all_operations()
    
    # Search operations
    print("\nPerforming search operations...")
    
    # Multi-criteria search
    print("\nPerforming multi-criteria search:")
    criteria_list = [
        {"name": "laptop", "fuzzy": True},
        {"price_range": {"min": 100, "max": 500}},
        {"category": "Electronics"},
        {"min_rating": 4.0}
    ]
    client.async_search_by_criteria(criteria_list)
    
    # Batch updates
    print("\nPerforming batch updates:")
    updates_list = [
        {
            "product_id": p["ID"],
            "update_data": {
                "Price": p["Price"] * 1.1,  # 10% price increase
                "StockQty": p["StockQty"] + 10
            }
        }
        for p in products[:3]
    ]
    client.async_batch_updates(updates_list)
    
    # Bulk price updates
    print("\nPerforming bulk price updates:")
    price_adjustments = [
        {"product_id": p["ID"], "new_price": p["Price"] * 0.9}  # 10% price decrease
        for p in products[3:6]
    ]
    client.async_bulk_price_updates(price_adjustments)
    
    # Wait for all operations to complete
    print("\nWaiting for all async operations to complete...")
    results = client.wait_for_all_operations()
    print(f"Completed {len(results)} async operations")

def main():
    """Run both synchronous and asynchronous demos."""
    print("Starting ElasticSearch client demos...")
    
    # Run synchronous demo
    start_time = time.time()
    demo_sync_client()
    sync_duration = time.time() - start_time
    print(f"\nSynchronous demo completed in {sync_duration:.2f} seconds")
    
    # Run asynchronous demo
    start_time = time.time()
    demo_async_client()
    async_duration = time.time() - start_time
    print(f"\nAsynchronous demo completed in {async_duration:.2f} seconds")
    
    print(f"\nPerformance comparison:")
    print(f"Synchronous duration: {sync_duration:.2f} seconds")
    print(f"Asynchronous duration: {async_duration:.2f} seconds")
    print(f"Speedup: {sync_duration/async_duration:.2f}x")

if __name__ == "__main__":
    main() 