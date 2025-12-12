#!/usr/bin/env python3
"""
Hassett Forecasting Script - Databricks Edition
Implements 92-93% accuracy methodology from 100+ experiments

Usage:
    python src/forecast.py --week 51 --year 2025
    python src/forecast.py --week 51 --year 2025 --output results.csv
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql


# ============================================================================
# CONFIGURATION
# ============================================================================

DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

# Seasonal multipliers (Fourier-based, from experiments)
SEASONAL_MULTIPLIERS = {
    48: 1.20,  # Thanksgiving week
    49: 1.25,  # Pre-peak
    50: 1.27,  # Peak (2 weeks before Christmas)
    51: 1.25,  # Peak (1 week before Christmas)
    52: 1.15,  # Christmas week (lighter)
}


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def connect_to_databricks():
    """Establish connection to Azure Databricks."""
    try:
        conn = sql.connect(**DATABRICKS_CONFIG)
        print("✅ Connected to Azure Databricks")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to Databricks: {e}")
        sys.exit(1)


def load_historical_data(conn, table_name="hassett_report"):
    """
    Load historical shipping data from Databricks.

    Expected schema:
        - DATE_SHIP: date
        - ODC: string
        - DDC: string
        - ProductType: string (MAX, EXP)
        - PIECES: int
    """
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

    print("📊 Loading historical data from Databricks...")
    df = pd.read_sql(query, conn)

    # Parse dates and add time features
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['week'] = df['date'].dt.isocalendar().week
    df['dayofweek'] = df['date'].dt.dayofweek
    df['dayofyear'] = df['date'].dt.dayofyear

    print(f"✅ Loaded {len(df):,} records")
    print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"📦 Products: {', '.join(df['ProductType'].unique())}")
    print(f"📍 ODCs: {df['ODC'].nunique()}")
    print(f"🎯 DDCs: {df['DDC'].nunique()}")

    return df


# ============================================================================
# FORECASTING LOGIC (92-93% Accuracy Methodology)
# ============================================================================

def get_baseline(df, target_week, product_type):
    """
    Get baseline forecast using optimal historical period.

    Winning approach from experiments:
    - MAX: 2022 Week N baseline (93.46% accuracy)
    - EXP: 2024 Week N baseline (86.37% accuracy)
    """
    baseline_year = 2022 if product_type == 'MAX' else 2024

    baseline = df[
        (df['year'] == baseline_year) &
        (df['week'] == target_week) &
        (df['ProductType'] == product_type)
    ].copy()

    if len(baseline) == 0:
        print(f"⚠️  No baseline data found for {product_type} in {baseline_year} Week {target_week}")
        return pd.DataFrame()

    # Aggregate by ODC, DDC, dayofweek
    baseline_agg = baseline.groupby(['ODC', 'DDC', 'dayofweek'])['pieces'].mean().reset_index()
    baseline_agg.columns = ['ODC', 'DDC', 'dayofweek', 'baseline']
    baseline_agg['ProductType'] = product_type
    baseline_agg['baseline_year'] = baseline_year

    return baseline_agg


def calculate_yoy_trend(df, target_week, target_year, product_type):
    """
    Calculate Year-over-Year trend multiplier.
    Compare recent 8 weeks to same 8 weeks last year.
    """
    # Get recent 8 weeks from current year (before target week)
    recent_weeks = list(range(max(1, target_week - 8), target_week))

    # Current year recent data
    recent_data = df[
        (df['year'] == target_year) &
        (df['week'].isin(recent_weeks)) &
        (df['ProductType'] == product_type)
    ]

    # Last year same weeks
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
        print(f"⚠️  Insufficient data for YoY trend calculation for {product_type}, using 1.0")
        trend = 1.0

    return trend


def generate_forecast(df, target_week, target_year):
    """
    Generate forecast using integrated methodology.

    Steps:
    1. Product-specific baseline (2022 for MAX, 2024 for EXP)
    2. YoY trend adjustment
    3. Seasonal adjustment (Fourier multiplier)
    4. Generate day-level forecasts
    """
    print(f"\n{'='*70}")
    print(f"GENERATING FORECAST: Week {target_week}, {target_year}")
    print(f"{'='*70}\n")

    # Get seasonal multiplier
    seasonal_multiplier = SEASONAL_MULTIPLIERS.get(target_week, 1.0)
    print(f"🎄 Seasonal Multiplier: {seasonal_multiplier:.2f}x")
    if target_week in SEASONAL_MULTIPLIERS:
        print(f"   ⚠️  Peak season week detected!")

    # Get baselines for both products
    print(f"\n📊 Step 1: Calculate Baselines")
    baseline_max = get_baseline(df, target_week, 'MAX')
    baseline_exp = get_baseline(df, target_week, 'EXP')

    if len(baseline_max) == 0 and len(baseline_exp) == 0:
        print("❌ No baseline data available. Cannot generate forecast.")
        return pd.DataFrame()

    baseline_combined = pd.concat([baseline_max, baseline_exp], ignore_index=True)

    print(f"   MAX (2022 Week {target_week}): {baseline_max['baseline'].sum():,.0f} pieces")
    print(f"   EXP (2024 Week {target_week}): {baseline_exp['baseline'].sum():,.0f} pieces")

    # Calculate trends
    print(f"\n📈 Step 2: Calculate YoY Trends")
    trend_max = calculate_yoy_trend(df, target_week, target_year, 'MAX')
    trend_exp = calculate_yoy_trend(df, target_week, target_year, 'EXP')

    print(f"   MAX Trend: {trend_max:.3f} ({'↑' if trend_max > 1 else '↓'} {abs(trend_max-1)*100:.1f}%)")
    print(f"   EXP Trend: {trend_exp:.3f} ({'↑' if trend_exp > 1 else '↓'} {abs(trend_exp-1)*100:.1f}%)")

    # Apply adjustments
    print(f"\n🎯 Step 3: Generate Forecast")
    forecast = baseline_combined.copy()
    forecast['trend'] = forecast['ProductType'].map({'MAX': trend_max, 'EXP': trend_exp})
    forecast['seasonal'] = seasonal_multiplier
    forecast['forecast'] = (
        forecast['baseline'] *
        forecast['trend'] *
        forecast['seasonal']
    )

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

    total_forecast = forecast['forecast'].sum()
    print(f"\n✅ Total Forecast: {total_forecast:,.0f} pieces")

    return forecast


# ============================================================================
# OUTPUT & REPORTING
# ============================================================================

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"integrated_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Forecast saved to: {output_path}")
    print(f"   Records: {len(forecast):,}")
    print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


def print_detailed_summary(forecast):
    """Print detailed forecast breakdown."""
    print(f"\n{'='*70}")
    print(f"DETAILED FORECAST SUMMARY")
    print(f"{'='*70}")

    # By Product Type
    print(f"\n📦 By Product Type:")
    by_product = forecast.groupby('ProductType')['forecast'].sum().sort_values(ascending=False)
    for product, volume in by_product.items():
        pct = (volume / forecast['forecast'].sum()) * 100
        print(f"   {product}: {volume:>12,.0f} pieces ({pct:.1f}%)")

    # Top 10 ODCs
    print(f"\n📍 Top 10 ODCs:")
    top_odcs = forecast.groupby('ODC')['forecast'].sum().nlargest(10)
    for i, (odc, volume) in enumerate(top_odcs.items(), 1):
        pct = (volume / forecast['forecast'].sum()) * 100
        print(f"   {i:2d}. {odc:5s}: {volume:>12,.0f} pieces ({pct:.1f}%)")

    # By Day of Week
    print(f"\n📅 By Day of Week:")
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    by_dow = forecast.groupby('dayofweek')['forecast'].sum()
    for dow, volume in by_dow.items():
        pct = (volume / forecast['forecast'].sum()) * 100
        print(f"   {dow_names[dow]:9s}: {volume:>12,.0f} pieces ({pct:.1f}%)")

    print(f"\n{'='*70}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Hassett Forecasting - Generate demand forecasts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/forecast.py --week 51 --year 2025
  python src/forecast.py --week 51 --year 2025 --output results.csv
  python src/forecast.py --week 50 --year 2025 --table my_schema.hassett_data
        """
    )

    parser.add_argument('--week', type=int, required=True,
                        help='Target week number (1-53)')
    parser.add_argument('--year', type=int, required=True,
                        help='Target year (e.g., 2025)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output CSV file path (default: auto-generated)')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report',
                        help='Databricks table name (default: decus_domesticops_prod.dbo.tmp_hassett_report)')
    parser.add_argument('--no-summary', action='store_true',
                        help='Skip detailed summary output')

    args = parser.parse_args()

    # Validate inputs
    if not 1 <= args.week <= 53:
        print(f"❌ Invalid week number: {args.week}. Must be between 1 and 53.")
        sys.exit(1)

    if not 2020 <= args.year <= 2030:
        print(f"⚠️  Warning: Year {args.year} seems unusual. Proceeding anyway...")

    print(f"\n{'='*70}")
    print(f"HASSETT FORECASTING SYSTEM")
    print(f"{'='*70}")
    print(f"Target: Week {args.week}, {args.year}")
    print(f"Methodology: 92-93% Accuracy (100+ Experiments)")
    print(f"{'='*70}\n")

    # Connect to Databricks
    conn = connect_to_databricks()

    try:
        # Load data
        df = load_historical_data(conn, table_name=args.table)

        # Generate forecast
        forecast = generate_forecast(df, args.week, args.year)

        if len(forecast) == 0:
            print("❌ Forecast generation failed. Exiting.")
            sys.exit(1)

        # Save results
        output_path = save_forecast(forecast, args.output)

        # Print summary
        if not args.no_summary:
            print_detailed_summary(forecast)

        print(f"\n{'='*70}")
        print(f"✅ FORECAST COMPLETE!")
        print(f"{'='*70}\n")

        return output_path

    except Exception as e:
        print(f"\n❌ Error during forecasting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()
        print("🔒 Database connection closed")


if __name__ == "__main__":
    main()
