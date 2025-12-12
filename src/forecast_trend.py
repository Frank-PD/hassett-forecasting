#!/usr/bin/env python3
"""
METHOD 2: Baseline + YoY Trend Forecast
Accuracy: Improved over baseline with trend adjustment

Adds Year-over-Year growth trends to baseline:
- MAX: 2022 Week N baseline + YoY trend
- EXP: 2024 Week N baseline + YoY trend
- NO seasonal adjustment (use Method 3 for that)
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
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

def load_historical_data(conn, table_name):
    """Load historical shipping data."""
    query = f"""
    SELECT
        DATE_SHIP as date,
        ODC,
        DDC,
        ProductType,
        PIECES as pieces
    FROM {table_name}
    WHERE ProductType IN ('MAX', 'EXP')
        AND DATE_SHIP IS NOT NULL
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP
    """

    print("📊 Loading historical data...")
    df = pd.read_sql(query, conn)

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['week'] = df['date'].dt.isocalendar().week
    df['dayofweek'] = df['date'].dt.dayofweek

    print(f"✅ Loaded {len(df):,} records")
    print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    return df

def calculate_yoy_trend(df, target_week, target_year, product_type):
    """
    Calculate Year-over-Year trend multiplier.
    Compare recent 8 weeks to same 8 weeks last year.
    """
    recent_weeks = list(range(max(1, target_week - 8), target_week))

    recent_data = df[
        (df['year'] == target_year) &
        (df['week'].isin(recent_weeks)) &
        (df['ProductType'] == product_type)
    ]

    lastyear_data = df[
        (df['year'] == target_year - 1) &
        (df['week'].isin(recent_weeks)) &
        (df['ProductType'] == product_type)
    ]

    if len(recent_data) > 0 and len(lastyear_data) > 0:
        recent_avg = recent_data['pieces'].mean()
        lastyear_avg = lastyear_data['pieces'].mean()
        trend = recent_avg / lastyear_avg if lastyear_avg > 0 else 1.0
    else:
        print(f"   ⚠️  Insufficient data for {product_type} trend, using 1.0")
        trend = 1.0

    return trend

def generate_trend_forecast(df, target_week, target_year):
    """
    METHOD 2: Baseline + YoY Trend

    1. Get historical baseline (2022 for MAX, 2024 for EXP)
    2. Calculate YoY growth trend
    3. Apply: Forecast = Baseline × Trend
    """
    print(f"\n{'='*70}")
    print(f"METHOD 2: BASELINE + YoY TREND FORECAST")
    print(f"Week {target_week}, {target_year}")
    print(f"{'='*70}\n")

    forecasts = []

    # MAX: 2022 baseline
    print("📊 MAX Product:")
    print("   Step 1: Get 2022 Week N baseline")
    max_baseline = df[
        (df['year'] == 2022) &
        (df['week'] == target_week) &
        (df['ProductType'] == 'MAX')
    ].copy()

    if len(max_baseline) > 0:
        max_agg = max_baseline.groupby(['ODC', 'DDC', 'dayofweek'])['pieces'].mean().reset_index()
        max_agg.columns = ['ODC', 'DDC', 'dayofweek', 'baseline']

        print(f"      ✅ Baseline: {max_agg['baseline'].sum():,.0f} pieces")

        # Calculate trend
        print("   Step 2: Calculate YoY trend")
        max_trend = calculate_yoy_trend(df, target_week, target_year, 'MAX')
        print(f"      📈 Trend: {max_trend:.3f} ({'↑' if max_trend > 1 else '↓'} {abs(max_trend-1)*100:.1f}%)")

        # Apply trend
        max_agg['trend'] = max_trend
        max_agg['forecast'] = max_agg['baseline'] * max_agg['trend']
        max_agg['ProductType'] = 'MAX'
        max_agg['baseline_year'] = 2022
        max_agg['method'] = 'Baseline_Plus_Trend'

        forecasts.append(max_agg)
        print(f"   ✅ Final: {max_agg['forecast'].sum():,.0f} pieces")
    else:
        print("   ⚠️  No 2022 MAX data found")

    # EXP: 2024 baseline
    print("\n📊 EXP Product:")
    print("   Step 1: Get 2024 Week N baseline")
    exp_baseline = df[
        (df['year'] == 2024) &
        (df['week'] == target_week) &
        (df['ProductType'] == 'EXP')
    ].copy()

    if len(exp_baseline) > 0:
        exp_agg = exp_baseline.groupby(['ODC', 'DDC', 'dayofweek'])['pieces'].mean().reset_index()
        exp_agg.columns = ['ODC', 'DDC', 'dayofweek', 'baseline']

        print(f"      ✅ Baseline: {exp_agg['baseline'].sum():,.0f} pieces")

        # Calculate trend
        print("   Step 2: Calculate YoY trend")
        exp_trend = calculate_yoy_trend(df, target_week, target_year, 'EXP')
        print(f"      📈 Trend: {exp_trend:.3f} ({'↑' if exp_trend > 1 else '↓'} {abs(exp_trend-1)*100:.1f}%)")

        # Apply trend
        exp_agg['trend'] = exp_trend
        exp_agg['forecast'] = exp_agg['baseline'] * exp_agg['trend']
        exp_agg['ProductType'] = 'EXP'
        exp_agg['baseline_year'] = 2024
        exp_agg['method'] = 'Baseline_Plus_Trend'

        forecasts.append(exp_agg)
        print(f"   ✅ Final: {exp_agg['forecast'].sum():,.0f} pieces")
    else:
        print("   ⚠️  No 2024 EXP data found")

    if len(forecasts) == 0:
        print("❌ No baseline data available")
        return pd.DataFrame()

    forecast = pd.concat(forecasts, ignore_index=True)
    forecast['week'] = target_week
    forecast['year'] = target_year

    # Summary
    print(f"\n📊 Forecast Summary:")
    summary = forecast.groupby('ProductType').agg({
        'baseline': 'sum',
        'forecast': 'sum'
    }).round(0)
    summary['change_%'] = ((summary['forecast'] - summary['baseline']) / summary['baseline'] * 100).round(1)
    print(summary.to_string())

    print(f"\n✅ Total Forecast: {forecast['forecast'].sum():,.0f} pieces")
    print(f"   (vs {forecast['baseline'].sum():,.0f} baseline = {((forecast['forecast'].sum() - forecast['baseline'].sum()) / forecast['baseline'].sum() * 100):+.1f}% change)")

    return forecast

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"trend_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="METHOD 2: Baseline + YoY Trend Forecast")
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"METHOD 2: BASELINE + YoY TREND FORECAST")
    print(f"Baseline (92-93%) + YoY Growth Adjustment")
    print(f"{'='*70}\n")

    conn = connect_to_databricks()

    try:
        df = load_historical_data(conn, args.table)
        forecast = generate_trend_forecast(df, args.week, args.year)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*70}")
            print(f"✅ FORECAST COMPLETE!")
            print(f"{'='*70}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
