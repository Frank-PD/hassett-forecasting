#!/usr/bin/env python3
"""
COMPARE FORECAST TO ACTUAL
Compare generated forecasts to actual shipments for performance tracking.

This script:
1. Loads forecast file (from run_local_forecast.py)
2. Loads actual shipment data
3. Joins on route/week
4. Calculates errors
5. Outputs comparison file for performance_tracker.py
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def load_forecasts(forecast_path):
    """Load forecast file."""

    print(f"📂 Loading forecasts: {forecast_path}")
    forecasts = pd.read_csv(forecast_path)

    # Ensure required columns
    required = ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'week_number', 'year', 'optimal_model', 'forecast']
    missing = [col for col in required if col not in forecasts.columns]

    if missing:
        print(f"⚠️  Warning: Missing columns in forecasts: {missing}")

    print(f"   ✅ Loaded {len(forecasts):,} forecast records")
    return forecasts

def load_actuals(actuals_path):
    """Load actual shipment data."""

    print(f"📂 Loading actuals: {actuals_path}")
    actuals = pd.read_csv(actuals_path)

    # Standardize column names
    actuals.columns = [
        'week_ending' if 'week' in col.lower() and 'ending' in col.lower() else
        'ProductType' if 'product' in col.lower() and 'type' in col.lower() else
        'ODC' if col == 'ODC' else
        'DDC' if col == 'DDC' else
        'pieces' if 'piece' in col.lower() else
        'dayofweek' if 'day' in col.lower() and 'index' in col.lower() else
        col for col in actuals.columns
    ]

    print(f"   ✅ Loaded {len(actuals):,} actual records")
    return actuals

def join_forecast_and_actual(forecasts, actuals):
    """Join forecasts with actuals."""

    print(f"\n🔗 Joining forecasts with actuals...")

    # Join on route identifiers
    comparison = forecasts.merge(
        actuals[['ODC', 'DDC', 'ProductType', 'dayofweek', 'pieces']],
        on=['ODC', 'DDC', 'ProductType', 'dayofweek'],
        how='left'
    )

    comparison = comparison.rename(columns={'pieces': 'actual_value'})
    comparison['forecast_value'] = comparison['forecast']

    # Calculate errors
    comparison['error_pct'] = (
        (comparison['forecast_value'] - comparison['actual_value']) /
        comparison['actual_value'] * 100
    ).replace([np.inf, -np.inf], 0)

    comparison['absolute_error_pct'] = comparison['error_pct'].abs()

    # Filter to routes with actuals
    routes_with_actuals = comparison[comparison['actual_value'].notna() & (comparison['actual_value'] > 0)]
    routes_without_actuals = comparison[comparison['actual_value'].isna() | (comparison['actual_value'] == 0)]

    print(f"   ✅ Matched {len(routes_with_actuals):,} routes with actuals")
    print(f"   ⚠️  {len(routes_without_actuals):,} routes without actuals (will be excluded)")

    return routes_with_actuals

def calculate_metrics(comparison):
    """Calculate performance metrics."""

    print(f"\n📊 Performance Metrics:")

    avg_mape = comparison['absolute_error_pct'].mean()
    median_mape = comparison['absolute_error_pct'].median()
    routes_under_20 = (comparison['absolute_error_pct'] < 20).sum()
    routes_under_50 = (comparison['absolute_error_pct'] < 50).sum()

    print(f"   Average MAPE: {avg_mape:.1f}%")
    print(f"   Median MAPE: {median_mape:.1f}%")
    print(f"   Routes <20% error: {routes_under_20:,} ({routes_under_20/len(comparison)*100:.1f}%)")
    print(f"   Routes <50% error: {routes_under_50:,} ({routes_under_50/len(comparison)*100:.1f}%)")

    # Performance by model
    print(f"\n📊 Performance by Model:")
    model_performance = comparison.groupby('optimal_model').agg({
        'absolute_error_pct': ['mean', 'median', 'count']
    }).round(1)

    model_performance.columns = ['Avg_MAPE', 'Median_MAPE', 'Routes']
    model_performance = model_performance.sort_values('Avg_MAPE')

    for model, row in model_performance.head(10).iterrows():
        print(f"   {model:<40} {row['Routes']:>5.0f} routes, Avg: {row['Avg_MAPE']:>6.1f}%, Median: {row['Median_MAPE']:>6.1f}%")

    return {
        'avg_mape': avg_mape,
        'median_mape': median_mape,
        'routes_under_20': routes_under_20,
        'routes_under_50': routes_under_50
    }

def prepare_for_performance_tracker(comparison):
    """Prepare comparison data for performance_tracker.py."""

    print(f"\n📝 Preparing for performance tracker...")

    # Rename columns to match performance_tracker expectations
    output = comparison[[
        'route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek',
        'week_number', 'year', 'optimal_model',
        'forecast_value', 'actual_value', 'error_pct', 'absolute_error_pct'
    ]].copy()

    # Rename model column
    output = output.rename(columns={'optimal_model': 'model_name'})

    print(f"   ✅ Prepared {len(output):,} records for performance tracker")

    return output

def save_comparison(comparison, output_path):
    """Save comparison file."""

    comparison.to_csv(output_path, index=False)
    print(f"\n✅ Comparison saved: {output_path}")
    print(f"   Columns: {', '.join(comparison.columns)}")

def main():
    parser = argparse.ArgumentParser(description="Compare Forecast to Actual")
    parser.add_argument('--forecasts', type=str, required=True,
                       help='Path to forecast CSV (from run_local_forecast.py)')
    parser.add_argument('--actuals', type=str, required=True,
                       help='Path to actual shipment data CSV')
    parser.add_argument('--output', type=str, required=True,
                       help='Output path for comparison CSV')
    args = parser.parse_args()

    print("=" * 80)
    print("COMPARE FORECAST TO ACTUAL")
    print("=" * 80)
    print()

    # Load data
    forecasts = load_forecasts(args.forecasts)
    actuals = load_actuals(args.actuals)

    # Join and calculate errors
    comparison = join_forecast_and_actual(forecasts, actuals)

    # Calculate metrics
    metrics = calculate_metrics(comparison)

    # Prepare for performance tracker
    output = prepare_for_performance_tracker(comparison)

    # Save
    save_comparison(output, args.output)

    print("\n" + "=" * 80)
    print("✅ COMPARISON COMPLETE")
    print("=" * 80)

    print(f"\n💡 Next Step:")
    print(f"   Record this week's performance in database:")
    print(f"   python3 src/performance_tracker.py \\")
    print(f"     --action record \\")
    print(f"     --week-results {args.output} \\")
    print(f"     --db local_performance_tracking.db")

if __name__ == "__main__":
    main()
