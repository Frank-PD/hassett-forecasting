#!/usr/bin/env python3
"""
PRODUCTION FORECAST GENERATOR
Takes comprehensive comparison output and generates clean production forecast.

Output includes:
- route_key, ODC, DDC, ProductType, dayofweek
- forecast (predicted count)
- optimal_model (which model was used)
- confidence (HIGH/MEDIUM/LOW based on historical error)
- forecast_low, forecast_high (confidence intervals)
- variance_pieces, variance_pct
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def calculate_confidence_level(error_pct):
    """
    Determine confidence level based on historical error.

    HIGH: <20% error
    MEDIUM: 20-50% error
    LOW: >50% error
    """
    error_abs = abs(error_pct)

    if error_abs < 20:
        return 'HIGH'
    elif error_abs < 50:
        return 'MEDIUM'
    else:
        return 'LOW'

def calculate_variance(forecast, confidence, historical_error_pct=None):
    """
    Calculate variance based on confidence level.

    HIGH: ±10% (or historical error if lower)
    MEDIUM: ±25%
    LOW: ±50%
    """
    if confidence == 'HIGH':
        if historical_error_pct is not None and abs(historical_error_pct) < 20:
            variance_pct = abs(historical_error_pct)
        else:
            variance_pct = 10.0
    elif confidence == 'MEDIUM':
        variance_pct = 25.0
    else:  # LOW
        variance_pct = 50.0

    variance_pieces = forecast * (variance_pct / 100)
    forecast_low = max(0, forecast - variance_pieces)
    forecast_high = forecast + variance_pieces

    return forecast_low, forecast_high, variance_pieces, variance_pct

def generate_production_forecast(comprehensive_csv, output_csv, week_number, year):
    """
    Generate production-ready forecast from comprehensive comparison.
    """

    print("=" * 80)
    print(f"PRODUCTION FORECAST GENERATOR - Week {week_number}, {year}")
    print("=" * 80)

    # Load comprehensive comparison
    print(f"\n📂 Loading comprehensive comparison: {comprehensive_csv}")
    df = pd.read_csv(comprehensive_csv)
    print(f"   ✅ Loaded {len(df):,} routes")

    # Extract winner information
    print(f"\n🏆 Extracting winner model forecasts...")

    production_forecasts = []

    for idx, row in df.iterrows():
        route_key = row['route_key']
        ODC = row['ODC']
        DDC = row['DDC']
        ProductType = row['ProductType']
        dayofweek = row['dayofweek']

        # Get winner model and its forecast
        winner_model = row.get('Winner_Model', '04_Recent_8W')
        winner_error = row.get('Winner_Error%', 0)

        # Get the winner's forecast value
        # Column name is like "01_Historical_Baseline"
        forecast = row.get(winner_model, 0)

        # If forecast is missing, try to find it in error columns
        if pd.isna(forecast) or forecast == 0:
            # Fallback to 04_Recent_8W
            forecast = row.get('04_Recent_8W', 0)
            winner_model = '04_Recent_8W'
            winner_error = row.get('04_Recent_8W_Error%', 0)

        # Calculate confidence
        confidence = calculate_confidence_level(winner_error)

        # Calculate variance
        forecast_low, forecast_high, variance_pieces, variance_pct = calculate_variance(
            forecast, confidence, winner_error
        )

        production_forecasts.append({
            'route_key': route_key,
            'ODC': ODC,
            'DDC': DDC,
            'ProductType': ProductType,
            'dayofweek': dayofweek,
            'week_number': week_number,
            'year': year,
            'forecast': round(forecast, 1),
            'optimal_model': winner_model,
            'confidence': confidence,
            'historical_error_pct': round(winner_error, 1),
            'forecast_low': round(forecast_low, 1),
            'forecast_high': round(forecast_high, 1),
            'variance_pieces': round(variance_pieces, 1),
            'variance_pct': round(variance_pct, 1)
        })

    # Create DataFrame
    production_df = pd.DataFrame(production_forecasts)

    # Save
    production_df.to_csv(output_csv, index=False)

    print(f"\n✅ Production forecast saved: {output_csv}")
    print(f"   Total routes: {len(production_df):,}")

    # Summary statistics
    print(f"\n📊 FORECAST SUMMARY")
    print("-" * 80)

    total_volume = production_df['forecast'].sum()
    avg_forecast = production_df['forecast'].mean()

    print(f"\nTotal forecasted volume: {total_volume:,.0f} pieces")
    print(f"Average per route: {avg_forecast:,.1f} pieces")

    # Confidence breakdown
    print(f"\n📊 Confidence Level Breakdown:")
    confidence_summary = production_df.groupby('confidence').agg({
        'route_key': 'count',
        'forecast': 'sum',
        'variance_pct': 'mean'
    }).round(1)

    confidence_summary.columns = ['Routes', 'Total_Volume', 'Avg_Variance%']

    for conf, row in confidence_summary.iterrows():
        pct_routes = (row['Routes'] / len(production_df)) * 100
        print(f"  {conf:<8}: {row['Routes']:>5,.0f} routes ({pct_routes:>5.1f}%), "
              f"{row['Total_Volume']:>8,.0f} pieces, ±{row['Avg_Variance%']:>4.1f}% variance")

    # Model usage breakdown
    print(f"\n📊 Model Usage:")
    model_summary = production_df['optimal_model'].value_counts().head(10)

    for model, count in model_summary.items():
        pct = (count / len(production_df)) * 100
        print(f"  {model:<30}: {count:>5,.0f} routes ({pct:>5.1f}%)")

    # Sample forecasts
    print(f"\n📊 Sample Production Forecasts:")
    print("-" * 80)

    sample = production_df[['route_key', 'forecast', 'forecast_low', 'forecast_high',
                           'optimal_model', 'confidence']].head(10)

    for idx, row in sample.iterrows():
        print(f"{row['route_key']:<35} {row['forecast']:>6.1f} pieces "
              f"[{row['forecast_low']:>6.1f} - {row['forecast_high']:>6.1f}]  "
              f"{row['optimal_model']:<25} {row['confidence']}")

    print("\n" + "=" * 80)
    print("✅ PRODUCTION FORECAST COMPLETE")
    print("=" * 80)

    print(f"\n📁 Output file: {output_csv}")
    print(f"\n💡 Columns included:")
    print(f"  - route_key, ODC, DDC, ProductType, dayofweek")
    print(f"  - week_number, year")
    print(f"  - forecast (predicted count)")
    print(f"  - optimal_model (which model was used)")
    print(f"  - confidence (HIGH/MEDIUM/LOW)")
    print(f"  - historical_error_pct (past performance)")
    print(f"  - forecast_low, forecast_high (confidence intervals)")
    print(f"  - variance_pieces, variance_pct (±X pieces, ±X%)")

    print(f"\n🎯 Ready for deployment!")

    return production_df

def main():
    parser = argparse.ArgumentParser(description="Generate Production Forecast from Comprehensive Comparison")
    parser.add_argument('--input', type=str, required=True,
                       help='Input comprehensive comparison CSV')
    parser.add_argument('--output', type=str, required=True,
                       help='Output production forecast CSV')
    parser.add_argument('--week', type=int, required=True,
                       help='Week number')
    parser.add_argument('--year', type=int, required=True,
                       help='Year')
    args = parser.parse_args()

    generate_production_forecast(args.input, args.output, args.week, args.year)

if __name__ == "__main__":
    main()
