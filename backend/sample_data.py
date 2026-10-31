"""
NexusAI - Sample Dataset Generator
Creates a realistic Kaggle-style retail & e-commerce transaction dataset
with Dates, Customers, Products, Categories, Regions, Sales, Profits, Discounts, and Quantities.
"""
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_dataset(output_path: Path, num_rows: int = 2500) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 1000:
        return output_path

    np.random.seed(42)
    
    categories_products = {
        "Consumer Electronics": [
            ("Noise-Cancelling Headphones", 199.99, 0.28),
            ("Smart Watch Pro", 249.99, 0.32),
            ("UltraHD 4K Monitor", 389.99, 0.24),
            ("Ergonomic Mechanical Keyboard", 119.99, 0.35),
            ("USB-C Thunderbolt Dock", 149.99, 0.40),
            ("Wireless Noise Earbuds", 89.99, 0.30)
        ],
        "Office & Furniture": [
            ("Ergonomic Mesh Chair", 299.99, 0.22),
            ("Electric Standing Desk", 499.99, 0.18),
            ("Steel Filing Cabinet", 169.99, 0.25),
            ("LED Monitor Desk Lamp", 49.99, 0.45),
            ("Acoustic Desk Privacy Panel", 89.99, 0.38)
        ],
        "Apparel & Footwear": [
            ("Performance Running Shoes", 129.99, 0.42),
            ("All-Weather Waterproof Jacket", 159.99, 0.46),
            ("Organic Cotton Hoodie", 69.99, 0.50),
            ("Merino Wool Base Layer", 54.99, 0.48),
            ("Commuter Travel Backpack", 99.99, 0.44)
        ],
        "Industrial & Logistics Supplies": [
            ("Heavy-Duty Thermal Label Printer", 229.99, 0.26),
            ("Barcode Scanner Wireless", 119.99, 0.36),
            ("Recycled Corrugated Box Kit (100pk)", 79.99, 0.30),
            ("Industrial Pallet Shrink Wrap", 45.99, 0.28)
        ]
    }

    regions_cities = {
        "North America": ["New York", "Chicago", "San Francisco", "Austin", "Toronto"],
        "Europe": ["London", "Berlin", "Paris", "Amsterdam", "Madrid"],
        "Asia-Pacific": ["Tokyo", "Singapore", "Sydney", "Mumbai", "Seoul"],
        "Latin America": ["São Paulo", "Mexico City", "Buenos Aires", "Bogotá"]
    }

    customers = [
        (f"CUST-{1000 + i}", f"Customer_{i}", np.random.choice(["Enterprise", "Small Business", "Consumer"]))
        for i in range(1, 180)
    ]

    base_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 9, 28)
    total_days = (end_date - base_date).days

    rows = []
    all_categories = list(categories_products.keys())
    all_regions = list(regions_cities.keys())

    for i in range(num_rows):
        order_id = f"ORD-{20250000 + i}"
        days_offset = np.random.randint(0, total_days)
        order_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        category = np.random.choice(all_categories, p=[0.38, 0.24, 0.22, 0.16])
        prod_tuple = categories_products[category][np.random.randint(len(categories_products[category]))]
        product_name, base_price, target_margin = prod_tuple
        
        region = np.random.choice(all_regions, p=[0.45, 0.28, 0.20, 0.07])
        city = np.random.choice(regions_cities[region])
        
        cust_id, cust_name, segment = customers[np.random.randint(len(customers))]
        
        quantity = np.random.choice([1, 2, 3, 4, 5, 8, 12], p=[0.42, 0.26, 0.14, 0.08, 0.05, 0.03, 0.02])
        discount_rate = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.25], p=[0.45, 0.20, 0.15, 0.10, 0.06, 0.04])
        
        gross_sales = round(quantity * base_price, 2)
        net_sales = round(gross_sales * (1.0 - discount_rate), 2)
        cost = gross_sales * (1.0 - target_margin)
        profit = round(net_sales - cost, 2)
        shipping_cost = round(8.50 + quantity * 2.20, 2)
        payment_method = np.random.choice(["Corporate Credit Card", "Wire Transfer", "PayPal", "Stripe Checkout"], p=[0.40, 0.30, 0.15, 0.15])

        rows.append({
            "Transaction_ID": order_id,
            "Order_Date": order_date,
            "Customer_ID": cust_id,
            "Customer_Name": cust_name,
            "Customer_Segment": segment,
            "Product_Name": product_name,
            "Category": category,
            "Region": region,
            "City": city,
            "Unit_Price": base_price,
            "Quantity_Sold": quantity,
            "Discount_Percent": round(discount_rate * 100, 1),
            "Total_Revenue": net_sales,
            "Net_Profit": profit,
            "Shipping_Cost": shipping_cost,
            "Payment_Method": payment_method
        })

    df = pd.DataFrame(rows)
    df.sort_values(by="Order_Date", inplace=True)
    df.to_csv(output_path, index=False)
    return output_path

if __name__ == "__main__":
    p = generate_sample_dataset(Path(__file__).parent / "data" / "sample_ecommerce.csv")
    print(f"Generated sample dataset at {p}")
