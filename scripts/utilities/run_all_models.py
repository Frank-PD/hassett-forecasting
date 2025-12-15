#!/usr/bin/env python3
"""
Run All 3 Forecast Models and Compare Results

This script runs all three forecasting methodologies:
1. Baseline Only (simplest)
2. Baseline + YoY Trend
3. Full Integrated (baseline + trend + seasonal)

Then creates a comparison report.
"""

import subprocess
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse

def run_forecast(script_name, week, year, output_dir):
    """Run a forecast script and return the output path."""
    print(f"\n{'='*70}")
    print(f"Running {script_name}...")
    print(f"{'='*70}")

    # Determine output filename based on model type
    model_name = script_name.replace('forecast_', '').replace('.py', '')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{model_name}_week_{week}_{year}_{timestamp}.csv"

    cmd = [
        'python',
        f'src/{script_name}',
        '--week', str(week),
        '--year', str(year),
        '--output', str(output_file)
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n✅ {model_name.upper()} complete!")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {model_name.upper()} failed: {e}")
        return None

def compare_forecasts(baseline_file, trend_file, integrated_file, week, year):
    """Compare the three forecast outputs."""
    print(f"\n{'='*70}")
    print(f"COMPARISON REPORT: Week {week}, {year}")
    print(f"{'='*70}\n")

    # Load all forecasts
    df_baseline = pd.read_csv(baseline_file) if baseline_file and baseline_file.exists() else None
    df_trend = pd.read_csv(trend_file) if trend_file and trend_file.exists() else None
    df_integrated = pd.read_csv(integrated_file) if integrated_file and integrated_file.exists() else None

    comparison_data = []

    # Overall totals
    print("📊 TOTAL FORECAST VOLUMES:\n")

    if df_baseline is not None:
        baseline_total = df_baseline['forecast'].sum()
        comparison_data.append({
            'Model': '1. Baseline Only',
            'Total_Pieces': f"{baseline_total:,.0f}",
            'Description': '2022 MAX + 2024 EXP baselines (no adjustments)'
        })
        print(f"   1. Baseline Only:      {baseline_total:>15,.0f} pieces")

    if df_trend is not None:
        trend_total = df_trend['forecast'].sum()
        comparison_data.append({
            'Model': '2. Baseline + Trend',
            'Total_Pieces': f"{trend_total:,.0f}",
            'Description': 'Baseline + YoY growth adjustment'
        })
        print(f"   2. Baseline + Trend:   {trend_total:>15,.0f} pieces")

        if df_baseline is not None:
            diff_pct = ((trend_total - baseline_total) / baseline_total * 100)
            print(f"      (vs Baseline: {diff_pct:+.1f}%)")

    if df_integrated is not None:
        integrated_total = df_integrated['forecast'].sum()
        comparison_data.append({
            'Model': '3. Full Integrated',
            'Total_Pieces': f"{integrated_total:,.0f}",
            'Description': 'Baseline + Trend + Seasonal (1.25x for Week 51)'
        })
        print(f"   3. Full Integrated:    {integrated_total:>15,.0f} pieces")

        if df_baseline is not None:
            diff_pct = ((integrated_total - baseline_total) / baseline_total * 100)
            print(f"      (vs Baseline: {diff_pct:+.1f}%)")

    # By product type
    print(f"\n📦 BY PRODUCT TYPE:\n")

    for product in ['MAX', 'EXP']:
        print(f"   {product}:")

        if df_baseline is not None:
            total = df_baseline[df_baseline['ProductType'] == product]['forecast'].sum()
            print(f"      Baseline:    {total:>12,.0f} pieces")

        if df_trend is not None:
            total = df_trend[df_trend['ProductType'] == product]['forecast'].sum()
            print(f"      + Trend:     {total:>12,.0f} pieces")

        if df_integrated is not None:
            total = df_integrated[df_integrated['ProductType'] == product]['forecast'].sum()
            print(f"      + Seasonal:  {total:>12,.0f} pieces")

        print()

    # Recommendations
    print(f"{'='*70}")
    print(f"RECOMMENDATIONS:")
    print(f"{'='*70}\n")

    print("📌 Which model to use?\n")
    print("   1. BASELINE ONLY - Use if:")
    print("      • You want the simplest, most stable forecast")
    print("      • Business is steady with no major trends")
    print("      • Expected accuracy: 92-93%\n")

    print("   2. BASELINE + TREND - Use if:")
    print("      • You're seeing growth or decline recently")
    print("      • Want to capture YoY momentum")
    print("      • Expected accuracy: 92-93% + trend adjustment\n")

    print("   3. FULL INTEGRATED - Use if:")
    print("      • Peak season weeks (48-52)")
    print("      • Want most comprehensive forecast")
    print("      • Need to account for seasonal patterns")
    print("      • Expected accuracy: 92-93% + adjustments\n")

    if week in [48, 49, 50, 51, 52]:
        print("   ⭐ RECOMMENDED: Full Integrated")
        print("      Reason: Week {} is peak season - seasonal adjustment needed\n".format(week))
    else:
        print("   ⭐ RECOMMENDED: Baseline + Trend")
        print("      Reason: Regular week - trend adjustment adds value\n")

    print(f"{'='*70}\n")

    # Save comparison report
    comparison_df = pd.DataFrame(comparison_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path('forecasts') / f"comparison_week_{week}_{year}_{timestamp}.csv"
    report_file.parent.mkdir(exist_ok=True)
    comparison_df.to_csv(report_file, index=False)

    print(f"💾 Comparison report saved to: {report_file}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Run all 3 forecast models and compare results"
    )
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output-dir', type=str, default='forecasts',
                        help='Output directory for forecasts (default: forecasts/)')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"HASSETT FORECASTING - MODEL COMPARISON")
    print(f"{'='*70}")
    print(f"Week: {args.week}")
    print(f"Year: {args.year}")
    print(f"Running all 3 models...")
    print(f"{'='*70}\n")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Run all three models
    baseline_file = run_forecast('forecast_baseline.py', args.week, args.year, output_dir)
    trend_file = run_forecast('forecast_trend.py', args.week, args.year, output_dir)
    integrated_file = run_forecast('forecast_integrated.py', args.week, args.year, output_dir)

    # Compare results
    compare_forecasts(baseline_file, trend_file, integrated_file, args.week, args.year)

    print(f"{'='*70}")
    print(f"✅ ALL MODELS COMPLETE!")
    print(f"{'='*70}")
    print(f"\nOutput files:")
    if baseline_file:
        print(f"   • {baseline_file}")
    if trend_file:
        print(f"   • {trend_file}")
    if integrated_file:
        print(f"   • {integrated_file}")
    print()

if __name__ == "__main__":
    main()
