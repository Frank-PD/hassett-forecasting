#!/usr/bin/env python3
"""
HYBRID HASSETT FORECASTING - Best of Both Worlds
Combines:
  1. Historical baseline (which routes ship in Week N)
  2. Recent activity validation (is route still active?)
  3. Recent data for magnitude (actual current volumes)
  4. Route-specific trends (route-level, not product-level)
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql

DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

def connect_to_databricks():
    """Establish connection to Azure Databricks."""
    try:
        conn = sql.connect(**DATABRICKS_CONFIG)
        print("✅ Connected to Azure Databricks")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def load_data(conn, target_week, target_year, table_name):
    """Load both historical baseline and recent activity."""

    # 1. Load historical baseline (which routes exist in Week N)
    baseline_year_max = 2022
    baseline_year_exp = 2024

    query_baseline = f"""
    SELECT
        ODC, DDC, ProductType, dayofweek(DATE_SHIP) as dayofweek,
        AVG(PIECES) as baseline_pieces,
        COUNT(*) as baseline_count
    FROM {table_name}
    WHERE weekofyear(DATE_SHIP) = {target_week}
        AND ((ProductType = 'MAX' AND YEAR(DATE_SHIP) = {baseline_year_max})
             OR (ProductType = 'EXP' AND YEAR(DATE_SHIP) = {baseline_year_exp}))
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    GROUP BY ODC, DDC, ProductType, dayofweek(DATE_SHIP)
    """

    print(f"📊 Loading historical baseline (Week {target_week})...")
    print(f"   MAX from {baseline_year_max}, EXP from {baseline_year_exp}")
    df_baseline = pd.read_sql(query_baseline, conn)
    print(f"✅ Loaded {len(df_baseline)} route-day combinations from baseline")

    # 2. Load RECENT activity (last 4 weeks)
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    recent_start = target_date - timedelta(weeks=4)

    query_recent = f"""
    SELECT
        ODC, DDC, ProductType, dayofweek(DATE_SHIP) as dayofweek,
        AVG(PIECES) as recent_avg,
        SUM(PIECES) as recent_total,
        COUNT(*) as recent_count
    FROM {table_name}
    WHERE DATE_SHIP >= '{recent_start.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    GROUP BY ODC, DDC, ProductType, dayofweek(DATE_SHIP)
    """

    print(f"\n📊 Loading recent activity (4 weeks before Week {target_week})...")
    print(f"   Date range: {recent_start.date()} to {target_date.date()}")
    df_recent = pd.read_sql(query_recent, conn)
    print(f"✅ Loaded {len(df_recent)} route-day combinations from recent data")

    return df_baseline, df_recent

def generate_hybrid_forecast(conn, target_week, target_year, table_name):
    """
    HYBRID APPROACH:
    1. Start with historical baseline routes
    2. Filter to only routes with recent activity
    3. Use recent data for magnitude
    4. Apply route-specific micro-trends
    """
    print(f"\n{'='*80}")
    print(f"HYBRID FORECASTING: Week {target_week}, {target_year}")
    print(f"{'='*80}\n")

    # Load data
    df_baseline, df_recent = load_data(conn, target_week, target_year, table_name)

    print(f"\n🔄 Merging baseline with recent activity...")

    # Merge baseline with recent data
    forecast = df_baseline.merge(
        df_recent,
        on=['ODC', 'DDC', 'ProductType', 'dayofweek'],
        how='left'  # Keep all baseline routes
    )

    # Filter: Only keep routes with recent activity
    forecast = forecast[forecast['recent_count'].notna() & (forecast['recent_count'] >= 1)]

    print(f"✅ After filtering:")
    print(f"   Routes in baseline: {len(df_baseline)}")
    print(f"   Routes with recent activity: {len(forecast)}")
    print(f"   Filtered out (dead routes): {len(df_baseline) - len(forecast)}")

    # Calculate forecast using RECENT data (not baseline)
    forecast['forecast'] = forecast['recent_avg']

    # Calculate confidence based on data recency
    forecast['confidence'] = np.minimum(forecast['recent_count'] / 3.0, 1.0)

    # Add metadata
    forecast['week'] = target_week
    forecast['year'] = target_year
    forecast['method'] = 'Hybrid_Baseline_Recent'

    # Calculate how much baseline vs recent differ
    forecast['baseline_vs_recent'] = ((forecast['recent_avg'] - forecast['baseline_pieces']) /
                                       forecast['baseline_pieces'] * 100)

    # Summary
    print(f"\n✅ Forecast Generated:")
    print(f"   Total routes: {len(forecast)}")
    print(f"   Total pieces: {forecast['forecast'].sum():,.0f}")

    print(f"\n📊 By Product:")
    for product in ['MAX', 'EXP']:
        product_forecast = forecast[forecast['ProductType'] == product]['forecast'].sum()
        product_routes = len(forecast[forecast['ProductType'] == product])
        print(f"   {product}: {product_forecast:,.0f} pieces ({product_routes} routes)")

    print(f"\n📈 Baseline vs Recent Comparison:")
    total_baseline = forecast['baseline_pieces'].sum()
    total_recent = forecast['recent_avg'].sum()
    print(f"   Historical baseline would be: {total_baseline:,.0f} pieces")
    print(f"   Using recent data: {total_recent:,.0f} pieces")
    print(f"   Adjustment: {(total_recent - total_baseline) / total_baseline * 100:+.1f}%")

    return forecast

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"hybrid_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="HYBRID: Baseline + Recent Activity Forecasting")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"HYBRID HASSETT FORECASTING")
    print(f"Historical Baseline + Recent Activity Validation")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_hybrid_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ HYBRID FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
