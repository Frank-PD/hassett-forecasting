#!/usr/bin/env python3
"""
PREPARE TEST ROUTES
Extract sample routes from routing table or historical data for local testing.
"""

import pandas as pd
import argparse

def extract_routes_from_routing_table(routing_table_path, num_routes=50, output_path='test_routes.csv'):
    """Extract sample routes from routing table."""

    print(f"📂 Loading routing table: {routing_table_path}")
    routing_table = pd.read_csv(routing_table_path)

    # Get unique routes
    routes = routing_table[['ODC', 'DDC', 'ProductType', 'dayofweek']].drop_duplicates()

    # Sample if more than requested
    if len(routes) > num_routes:
        routes = routes.sample(n=num_routes, random_state=42)

    # Save
    routes.to_csv(output_path, index=False)

    print(f"✅ Extracted {len(routes):,} routes to {output_path}")
    print(f"\n📊 Sample:")
    print(routes.head(10).to_string(index=False))

    return routes

def extract_all_routes_from_routing_table(routing_table_path, output_path='all_routes.csv'):
    """Extract ALL routes from routing table."""

    print(f"📂 Loading routing table: {routing_table_path}")
    routing_table = pd.read_csv(routing_table_path)

    # Get unique routes
    routes = routing_table[['ODC', 'DDC', 'ProductType', 'dayofweek']].drop_duplicates()

    # Save
    routes.to_csv(output_path, index=False)

    print(f"✅ Extracted {len(routes):,} routes to {output_path}")

    return routes

def main():
    parser = argparse.ArgumentParser(description="Prepare Routes for Testing")
    parser.add_argument('--routing-table', type=str, default='route_model_routing_table.csv',
                       help='Path to routing table')
    parser.add_argument('--num-routes', type=int, default=50,
                       help='Number of sample routes (0 = all routes)')
    parser.add_argument('--output', type=str, default='test_routes.csv',
                       help='Output path for routes CSV')
    args = parser.parse_args()

    print("=" * 80)
    print("PREPARE TEST ROUTES")
    print("=" * 80)
    print()

    if args.num_routes == 0:
        extract_all_routes_from_routing_table(args.routing_table, args.output)
    else:
        extract_routes_from_routing_table(args.routing_table, args.num_routes, args.output)

    print(f"\n💡 Next Step:")
    print(f"   python3 run_local_forecast.py \\")
    print(f"     --routing-table route_model_routing_table.csv \\")
    print(f"     --historical-data \"<path_to_historical_data.csv>\" \\")
    print(f"     --routes-to-forecast {args.output} \\")
    print(f"     --actuals \"<path_to_actuals.csv>\" \\")
    print(f"     --output local_forecasts.csv")

if __name__ == "__main__":
    main()
