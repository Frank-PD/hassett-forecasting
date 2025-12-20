#!/usr/bin/env python3
"""
Backfill Training Data - Run models for multiple historical weeks
Seeds the performance tracking database with historical data

Usage:
    python3 backfill_training_data.py --weeks 10

This will run all 14 models for the past 10 weeks and record results
to the SQLite database for routing table updates.

Estimated runtime: 30-60 minutes per week (5-10 hours for 10 weeks)
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from databricks import sql
import json
import warnings
warnings.filterwarnings('ignore')

from tqdm.auto import tqdm

# Add src to path
project_root = Path.cwd()
sys.path.insert(0, str(project_root / 'src'))

from forecast_comprehensive_all_models import ComprehensiveModels
from performance_tracker import PerformanceTracker

# Databricks config
DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

TABLE_NAME = "decus_domesticops_prod.dbo.tmp_hassett_report"

# All 14 models (excluding 15-18 which had 0 wins)
MODEL_FUNCTIONS = [
    ('01_Historical_Baseline', ComprehensiveModels.model_01_historical_baseline),
    ('02_Recent_2W', ComprehensiveModels.model_02_recent_2w_avg),
    ('03_Recent_4W_HYBRID', ComprehensiveModels.model_03_recent_4w_avg),
    ('04_Recent_8W', ComprehensiveModels.model_04_recent_8w_avg),
    ('05_Trend_Adjusted', ComprehensiveModels.model_05_trend_adjusted),
    ('06_Prior_Week', ComprehensiveModels.model_06_prior_week),
    ('07_Same_Week_Last_Year', ComprehensiveModels.model_07_same_week_last_year),
    ('08_Week_Specific', ComprehensiveModels.model_08_week_specific_historical),
    ('09_Exp_Smoothing', ComprehensiveModels.model_09_exponential_smoothing),
    ('10_Probabilistic', ComprehensiveModels.model_10_probabilistic),
    ('11_Hybrid_Week_Blend', ComprehensiveModels.model_11_hybrid_week_blend),
    ('12_Median_Recent', ComprehensiveModels.model_12_median_recent),
    ('13_Weighted_Recent_Week', ComprehensiveModels.model_13_weighted_recent_week),
    ('14_SARIMA', ComprehensiveModels.model_14_sarima),
]


def load_historical_data(conn, target_week, target_year, years=4):
    """Load historical data up to the target week."""
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    lookback_date = target_date - timedelta(days=365 * years)

    query = f"""
    SELECT
        DATE_SHIP as date,
        ODC, DDC, ProductType,
        PIECES as pieces,
        weekofyear(DATE_SHIP) as week,
        YEAR(DATE_SHIP) as year,
        dayofweek(DATE_SHIP) as dayofweek
    FROM {TABLE_NAME}
    WHERE DATE_SHIP >= '{lookback_date.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_week_actuals(conn, week, year):
    """Get actuals for a specific week."""
    query = f"""
    SELECT
        ODC,
        DDC,
        ProductType,
        dayofweek(DATE_SHIP) as dayofweek,
        SUM(PIECES) as actual_pieces
    FROM {TABLE_NAME}
    WHERE weekofyear(DATE_SHIP) = {week}
        AND YEAR(DATE_SHIP) = {year}
        AND ProductType IN ('MAX', 'EXP')
    GROUP BY ODC, DDC, ProductType, dayofweek(DATE_SHIP)
    ORDER BY ODC, DDC, ProductType, dayofweek
    """

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def process_single_week(conn, tracker, week, year, model_functions):
    """Process a single week - run all models and record results."""

    print(f"\n{'='*80}")
    print(f"PROCESSING WEEK {week}, {year}")
    print(f"{'='*80}")

    # Load historical data
    print(f"  Loading historical data...")
    df_historical = load_historical_data(conn, week, year)
    print(f"  Loaded {len(df_historical):,} historical records")

    # Get actuals
    print(f"  Loading actuals...")
    df_actuals = get_week_actuals(conn, week, year)
    print(f"  Found {len(df_actuals):,} route-day actuals")

    if len(df_actuals) == 0:
        print(f"  WARNING: No actuals found for week {week}, {year} - skipping")
        return None

    # Get routes
    routes = df_actuals[['ODC', 'DDC', 'ProductType', 'dayofweek']].drop_duplicates()
    print(f"  Generating forecasts for {len(routes):,} routes using {len(model_functions)} models...")

    # Generate forecasts
    results = []
    pbar = tqdm(routes.iterrows(), total=len(routes), desc=f"Week {week}")

    for idx, route in pbar:
        odc, ddc, product, dow = route['ODC'], route['DDC'], route['ProductType'], route['dayofweek']
        pbar.set_postfix({'Route': f"{odc}-{ddc}-{product}"})

        # Get route history
        route_data = df_historical[
            (df_historical['ODC'] == odc) &
            (df_historical['DDC'] == ddc) &
            (df_historical['ProductType'] == product) &
            (df_historical['dayofweek'] == dow)
        ].sort_values('date', ascending=False)

        # Get actual
        actual_row = df_actuals[
            (df_actuals['ODC'] == odc) &
            (df_actuals['DDC'] == ddc) &
            (df_actuals['ProductType'] == product) &
            (df_actuals['dayofweek'] == dow)
        ]
        actual = actual_row['actual_pieces'].values[0] if len(actual_row) > 0 else 0

        result = {
            'route_key': f"{odc}|{ddc}|{product}|{dow}",
            'ODC': odc,
            'DDC': ddc,
            'ProductType': product,
            'dayofweek': dow,
            'Actual': actual
        }

        # Run each model
        for model_name, model_func in model_functions:
            try:
                forecast = model_func(route_data, week, year, product)
                result[model_name] = max(0, forecast)
            except Exception as e:
                result[model_name] = 0

        results.append(result)

    df_forecasts = pd.DataFrame(results)

    # Calculate errors
    model_cols = [col for col in df_forecasts.columns
                  if col not in ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual']]

    for col in model_cols:
        error_col = f"{col}_Error%"
        df_forecasts[error_col] = np.where(
            df_forecasts['Actual'] > 0,
            abs((df_forecasts[col] - df_forecasts['Actual']) / df_forecasts['Actual'] * 100),
            np.where(df_forecasts[col] > 0, 999, 0)
        )

    # Find winners
    error_cols = [col for col in df_forecasts.columns if col.endswith('_Error%')]
    df_forecasts['Winner_Model'] = df_forecasts[error_cols].abs().idxmin(axis=1).str.replace('_Error%', '')
    df_forecasts['Winner_Error%'] = df_forecasts[error_cols].abs().min(axis=1)

    # Print summary
    win_summary = df_forecasts['Winner_Model'].value_counts()
    print(f"\n  Model wins for week {week}:")
    for model, count in win_summary.head(5).items():
        pct = count / len(df_forecasts) * 100
        print(f"    {model}: {count} ({pct:.1f}%)")

    # Record to database
    print(f"\n  Recording to database...")
    week_results = df_forecasts.copy()
    week_results['week_number'] = week
    week_results['year'] = year
    week_results['actual_value'] = week_results['Actual']

    tracker.record_week_performance(week_results)

    print(f"  Week {week} complete!")

    return df_forecasts


def main():
    parser = argparse.ArgumentParser(description="Backfill training data for routing table")
    parser.add_argument('--weeks', type=int, default=10, help='Number of weeks to backfill (default: 10)')
    parser.add_argument('--skip-sarima', action='store_true', help='Skip SARIMA model (faster)')
    args = parser.parse_args()

    # Calculate weeks to process
    today = datetime.now()
    current_week = today.isocalendar()[1]
    current_year = today.year

    # Start from last week and go backwards
    weeks_to_process = []
    week = current_week - 1
    year = current_year

    for i in range(args.weeks):
        if week < 1:
            week = 52
            year -= 1
        weeks_to_process.append((week, year))
        week -= 1

    # Reverse so we process oldest first
    weeks_to_process = weeks_to_process[::-1]

    print("="*80)
    print("BACKFILL TRAINING DATA")
    print("="*80)
    print(f"\nWill process {len(weeks_to_process)} weeks:")
    for w, y in weeks_to_process:
        print(f"  - Week {w}, {y}")

    # Select models
    model_functions = MODEL_FUNCTIONS.copy()
    if args.skip_sarima:
        model_functions = [(n, f) for n, f in model_functions if 'SARIMA' not in n]
        print(f"\nSkipping SARIMA - using {len(model_functions)} models")
    else:
        print(f"\nUsing all {len(model_functions)} models (including SARIMA)")

    print(f"\nEstimated runtime: {len(weeks_to_process) * 30}-{len(weeks_to_process) * 60} minutes")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")

    import time
    time.sleep(5)

    # Connect to Databricks
    print("\nConnecting to Databricks...")
    conn = sql.connect(**DATABRICKS_CONFIG)
    print("Connected!")

    # Initialize tracker
    db_path = project_root / 'data' / 'performance' / 'performance_tracking.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = PerformanceTracker(str(db_path))

    # Process each week
    start_time = datetime.now()
    successful_weeks = 0

    try:
        for week, year in weeks_to_process:
            week_start = datetime.now()
            result = process_single_week(conn, tracker, week, year, model_functions)

            if result is not None:
                successful_weeks += 1

            week_duration = datetime.now() - week_start
            print(f"\n  Week {week} took {week_duration.total_seconds() / 60:.1f} minutes")

            # Estimate remaining time
            elapsed = datetime.now() - start_time
            avg_per_week = elapsed / successful_weeks if successful_weeks > 0 else timedelta(minutes=30)
            remaining_weeks = len(weeks_to_process) - (weeks_to_process.index((week, year)) + 1)
            estimated_remaining = avg_per_week * remaining_weeks
            print(f"  Estimated remaining: {estimated_remaining.total_seconds() / 60:.0f} minutes")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
        print(f"Processed {successful_weeks} weeks before interruption")

    finally:
        conn.close()
        tracker.close()

    # Summary
    total_duration = datetime.now() - start_time
    print("\n" + "="*80)
    print("BACKFILL COMPLETE")
    print("="*80)
    print(f"\nProcessed {successful_weeks}/{len(weeks_to_process)} weeks")
    print(f"Total time: {total_duration.total_seconds() / 60:.1f} minutes")
    print(f"Database: {db_path}")
    print("\nYou can now run the weekly update script:")
    print("  python3 run_comprehensive_update.py")


if __name__ == "__main__":
    main()
