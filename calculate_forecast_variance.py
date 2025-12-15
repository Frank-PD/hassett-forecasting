#!/usr/bin/env python3
"""
CALCULATE FORECAST VARIANCE
Add confidence intervals to forecasts based on historical error and confidence level.

This script enhances forecast output with:
- forecast_low: Lower bound (pessimistic)
- forecast_high: Upper bound (optimistic)
- variance_pieces: ±X pieces
- variance_pct: ±X%
"""

import pandas as pd
import numpy as np
import argparse

def calculate_variance_from_historical_error(forecast, historical_error_pct):
    """
    Calculate variance based on historical error.

    If historical error is 10%, then forecast could be ±10%.
    """
    variance_pct = abs(historical_error_pct)
    variance_pieces = abs(forecast * (variance_pct / 100))

    forecast_low = max(0, forecast - variance_pieces)
    forecast_high = forecast + variance_pieces

    return forecast_low, forecast_high, variance_pieces, variance_pct

def calculate_variance_from_confidence(forecast, confidence, historical_error_pct=None):
    """
    Calculate variance based on confidence level.

    HIGH confidence: Use historical error or ±10% (whichever is lower)
    MEDIUM confidence: ±25%
    LOW confidence: ±50%
    NEW_ROUTE: ±100% (very uncertain)
    """

    if confidence == 'HIGH':
        # Use historical error if available and reasonable, else 10%
        if historical_error_pct is not None and abs(historical_error_pct) < 20:
            variance_pct = abs(historical_error_pct)
        else:
            variance_pct = 10.0

    elif confidence == 'MEDIUM':
        variance_pct = 25.0

    elif confidence == 'LOW':
        variance_pct = 50.0

    else:  # NEW_ROUTE or unknown
        variance_pct = 100.0

    variance_pieces = forecast * (variance_pct / 100)

    forecast_low = max(0, forecast - variance_pieces)
    forecast_high = forecast + variance_pieces

    return forecast_low, forecast_high, variance_pieces, variance_pct

def add_variance_to_forecasts(forecasts_df, method='confidence'):
    """
    Add variance columns to forecast dataframe.

    Args:
        forecasts_df: DataFrame with forecasts
        method: 'confidence' (use confidence levels) or 'historical' (use historical error)

    Returns:
        DataFrame with added variance columns
    """

    print(f"📊 Calculating variance using method: {method}")

    enhanced = forecasts_df.copy()

    # Initialize variance columns
    enhanced['forecast_low'] = 0.0
    enhanced['forecast_high'] = 0.0
    enhanced['variance_pieces'] = 0.0
    enhanced['variance_pct'] = 0.0

    for idx, row in enhanced.iterrows():
        forecast = row['forecast']
        confidence = row.get('confidence', 'LOW')
        historical_error = row.get('historical_error_pct', None)

        if method == 'confidence':
            low, high, var_pieces, var_pct = calculate_variance_from_confidence(
                forecast, confidence, historical_error
            )
        else:  # historical
            if historical_error is not None:
                low, high, var_pieces, var_pct = calculate_variance_from_historical_error(
                    forecast, historical_error
                )
            else:
                # Fallback to confidence method
                low, high, var_pieces, var_pct = calculate_variance_from_confidence(
                    forecast, confidence, None
                )

        enhanced.at[idx, 'forecast_low'] = round(low, 1)
        enhanced.at[idx, 'forecast_high'] = round(high, 1)
        enhanced.at[idx, 'variance_pieces'] = round(var_pieces, 1)
        enhanced.at[idx, 'variance_pct'] = round(var_pct, 1)

    return enhanced

def generate_summary_stats(enhanced_df):
    """Generate summary statistics by confidence level."""

    print("\n📊 Variance Summary by Confidence Level:")
    print("-" * 80)

    summary = enhanced_df.groupby('confidence').agg({
        'forecast': 'count',
        'variance_pct': ['mean', 'min', 'max'],
        'variance_pieces': ['mean', 'min', 'max']
    }).round(1)

    summary.columns = ['Routes', 'Avg_Var%', 'Min_Var%', 'Max_Var%', 'Avg_Var_Pcs', 'Min_Var_Pcs', 'Max_Var_Pcs']

    for conf, row in summary.iterrows():
        print(f"\n{conf}:")
        print(f"  Routes: {row['Routes']:.0f}")
        print(f"  Variance %: {row['Avg_Var%']:.1f}% (range: {row['Min_Var%']:.1f}% - {row['Max_Var%']:.1f}%)")
        print(f"  Variance pieces: ±{row['Avg_Var_Pcs']:.1f} (range: ±{row['Min_Var_Pcs']:.1f} - ±{row['Max_Var_Pcs']:.1f})")

def main():
    parser = argparse.ArgumentParser(description="Add Variance/Confidence Intervals to Forecasts")
    parser.add_argument('--input', type=str, required=True,
                       help='Input forecast CSV')
    parser.add_argument('--output', type=str, required=True,
                       help='Output forecast CSV with variance')
    parser.add_argument('--method', type=str, default='confidence',
                       choices=['confidence', 'historical'],
                       help='Variance calculation method')
    args = parser.parse_args()

    print("=" * 80)
    print("ADD VARIANCE TO FORECASTS")
    print("=" * 80)

    # Load forecasts
    print(f"\n📂 Loading forecasts: {args.input}")
    forecasts = pd.read_csv(args.input)
    print(f"   ✅ Loaded {len(forecasts):,} forecasts")

    # Add variance
    enhanced = add_variance_to_forecasts(forecasts, args.method)

    # Generate summary
    generate_summary_stats(enhanced)

    # Save
    enhanced.to_csv(args.output, index=False)
    print(f"\n✅ Enhanced forecasts saved: {args.output}")

    # Show sample
    print(f"\n📊 Sample Enhanced Forecasts:")
    print("-" * 80)

    sample = enhanced[['route_key', 'forecast', 'confidence', 'forecast_low', 'forecast_high',
                       'variance_pieces', 'variance_pct']].head(10)

    for idx, row in sample.iterrows():
        print(f"{row['route_key']:<30} {row['forecast']:>6.1f} pieces  "
              f"[{row['forecast_low']:>6.1f} - {row['forecast_high']:>6.1f}]  "
              f"±{row['variance_pieces']:>5.1f} ({row['variance_pct']:>4.1f}%)  "
              f"{row['confidence']}")

    print("\n" + "=" * 80)
    print("✅ VARIANCE CALCULATION COMPLETE")
    print("=" * 80)

    print(f"\nNew columns added:")
    print(f"  - forecast_low: Lower bound (pessimistic scenario)")
    print(f"  - forecast_high: Upper bound (optimistic scenario)")
    print(f"  - variance_pieces: ±X pieces")
    print(f"  - variance_pct: ±X%")

    print(f"\n💡 Usage:")
    print(f"  Forecast: {enhanced['forecast'].iloc[0]:.1f} pieces")
    print(f"  Range: {enhanced['forecast_low'].iloc[0]:.1f} - {enhanced['forecast_high'].iloc[0]:.1f} pieces")
    print(f"  Variance: ±{enhanced['variance_pieces'].iloc[0]:.1f} pieces (±{enhanced['variance_pct'].iloc[0]:.1f}%)")

if __name__ == "__main__":
    main()
