#!/usr/bin/env python3
"""
MULTI-MODEL BACKTESTING FRAMEWORK

Run EVERY forecasting model on EVERY route, then compare to actuals
to determine which model works best for each specific route.

Approach:
1. For each route, calculate forecasts using ALL available methods:
   - Historical baseline (Week N from previous years)
   - Recent 2-week average
   - Recent 4-week average
   - Recent 8-week average
   - Trend-adjusted recent
   - Prior week
   - Same week last year
   - Week-specific historical average
   - Exponential smoothing
   - Probabilistic (prior week × frequency)

2. Compare each model's forecast to actual

3. Select the model with lowest error for that route

4. Build a routing table: Route → Best Model

5. Use this for future forecasts
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql
import json

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

def load_historical_data(conn, target_week, target_year, table_name, years=4):
    """Load multi-year historical data."""
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
    FROM {table_name}
    WHERE DATE_SHIP >= '{lookback_date.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    print(f"📊 Loading {years} years of historical data...")
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    print(f"✅ Loaded {len(df):,} shipments")

    return df

class ForecastingModels:
    """Collection of all forecasting methods."""

    @staticmethod
    def model_01_historical_baseline(route_data, target_week, target_year, product):
        """Historical baseline: Week N from 2022/2024."""
        baseline_year = 2022 if product == 'MAX' else 2024
        baseline = route_data[
            (route_data['week'] == target_week) &
            (route_data['year'] == baseline_year)
        ]
        return baseline['pieces'].mean() if len(baseline) > 0 else 0

    @staticmethod
    def model_02_recent_2w_avg(route_data, target_week, target_year, product):
        """Recent 2-week average."""
        recent = route_data.head(2)
        return recent['pieces'].mean() if len(recent) >= 2 else 0

    @staticmethod
    def model_03_recent_4w_avg(route_data, target_week, target_year, product):
        """Recent 4-week average (Hybrid method)."""
        recent = route_data.head(4)
        return recent['pieces'].mean() if len(recent) >= 4 else 0

    @staticmethod
    def model_04_recent_8w_avg(route_data, target_week, target_year, product):
        """Recent 8-week average."""
        recent = route_data.head(8)
        return recent['pieces'].mean() if len(recent) >= 8 else 0

    @staticmethod
    def model_05_trend_adjusted(route_data, target_week, target_year, product):
        """Trend-adjusted: recent avg × trend factor."""
        if len(route_data) < 8:
            return route_data.head(4)['pieces'].mean() if len(route_data) >= 4 else 0

        recent_4 = route_data.head(4)['pieces'].mean()
        older_4 = route_data.iloc[4:8]['pieces'].mean()

        if older_4 > 0:
            trend_factor = recent_4 / older_4
            trend_factor = max(0.5, min(1.5, trend_factor))  # Cap at ±50%
            return recent_4 * trend_factor
        return recent_4

    @staticmethod
    def model_06_prior_week(route_data, target_week, target_year, product):
        """Prior week value."""
        prior_week = target_week - 1
        prior = route_data[route_data['week'] == prior_week]
        return prior['pieces'].mean() if len(prior) > 0 else 0

    @staticmethod
    def model_07_same_week_last_year(route_data, target_week, target_year, product):
        """Same week from last year."""
        last_year = target_year - 1
        same_week = route_data[
            (route_data['week'] == target_week) &
            (route_data['year'] == last_year)
        ]
        return same_week['pieces'].mean() if len(same_week) > 0 else 0

    @staticmethod
    def model_08_week_specific_historical(route_data, target_week, target_year, product):
        """Historical average for this specific week across all years."""
        week_data = route_data[route_data['week'] == target_week]
        return week_data['pieces'].mean() if len(week_data) >= 2 else 0

    @staticmethod
    def model_09_exponential_smoothing(route_data, target_week, target_year, product):
        """Exponential smoothing: weight recent more heavily."""
        if len(route_data) < 4:
            return route_data['pieces'].mean() if len(route_data) > 0 else 0

        # Weights: 0.4, 0.3, 0.2, 0.1 for last 4 weeks
        weights = np.array([0.4, 0.3, 0.2, 0.1])
        recent_4 = route_data.head(4)['pieces'].values

        if len(recent_4) == 4:
            return np.sum(recent_4 * weights)
        else:
            return recent_4.mean()

    @staticmethod
    def model_10_probabilistic(route_data, target_week, target_year, product):
        """Probabilistic: prior week × shipping probability."""
        prior_week = target_week - 1
        prior = route_data[route_data['week'] == prior_week]
        prior_value = prior['pieces'].mean() if len(prior) > 0 else 0

        # Shipping probability based on frequency in last 12 weeks
        recent_12w = route_data.head(12)
        ship_prob = min(len(recent_12w) / 12, 1.0)

        return prior_value * ship_prob

    @staticmethod
    def model_11_hybrid_week_blend(route_data, target_week, target_year, product):
        """Blend: 70% week-specific + 30% recent average."""
        week_avg = ForecastingModels.model_08_week_specific_historical(
            route_data, target_week, target_year, product
        )
        recent_avg = ForecastingModels.model_03_recent_4w_avg(
            route_data, target_week, target_year, product
        )

        if week_avg > 0 and recent_avg > 0:
            return 0.7 * week_avg + 0.3 * recent_avg
        elif week_avg > 0:
            return week_avg
        else:
            return recent_avg

    @staticmethod
    def model_12_median_recent(route_data, target_week, target_year, product):
        """Median of recent 4 weeks (robust to outliers)."""
        recent = route_data.head(4)
        return recent['pieces'].median() if len(recent) >= 4 else 0

    @staticmethod
    def model_13_weighted_recent_week(route_data, target_week, target_year, product):
        """Weighted blend: 50% recent + 50% week-specific."""
        recent = ForecastingModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)
        week_specific = ForecastingModels.model_08_week_specific_historical(route_data, target_week, target_year, product)

        if recent > 0 and week_specific > 0:
            return 0.5 * recent + 0.5 * week_specific
        elif recent > 0:
            return recent
        else:
            return week_specific

def run_all_models_for_route(route_data, target_week, target_year, product):
    """
    Run ALL forecasting models for a single route.

    Returns: dict of {model_name: forecast_value}
    """
    models = ForecastingModels()

    # Get all model methods
    model_methods = [
        ('01_historical_baseline', models.model_01_historical_baseline),
        ('02_recent_2w_avg', models.model_02_recent_2w_avg),
        ('03_recent_4w_avg', models.model_03_recent_4w_avg),
        ('04_recent_8w_avg', models.model_04_recent_8w_avg),
        ('05_trend_adjusted', models.model_05_trend_adjusted),
        ('06_prior_week', models.model_06_prior_week),
        ('07_same_week_last_year', models.model_07_same_week_last_year),
        ('08_week_specific_historical', models.model_08_week_specific_historical),
        ('09_exponential_smoothing', models.model_09_exponential_smoothing),
        ('10_probabilistic', models.model_10_probabilistic),
        ('11_hybrid_week_blend', models.model_11_hybrid_week_blend),
        ('12_median_recent', models.model_12_median_recent),
        ('13_weighted_recent_week', models.model_13_weighted_recent_week),
    ]

    forecasts = {}
    for model_name, model_func in model_methods:
        try:
            forecast = model_func(route_data, target_week, target_year, product)
            forecasts[model_name] = max(0, forecast)  # Never negative
        except Exception as e:
            forecasts[model_name] = 0

    return forecasts

def generate_multi_model_forecasts(conn, target_week, target_year, table_name):
    """
    Generate forecasts using ALL models for ALL routes.
    """
    print(f"\n{'='*80}")
    print(f"MULTI-MODEL BACKTESTING: Week {target_week}, {target_year}")
    print(f"Running ALL models on ALL routes")
    print(f"{'='*80}\n")

    # Load historical data
    df = load_historical_data(conn, target_week, target_year, table_name, years=4)

    # Get all unique routes from recent 12 weeks
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    recent_cutoff = target_date - timedelta(weeks=12)

    recent_routes = df[df['date'] >= recent_cutoff].groupby(
        ['ODC', 'DDC', 'ProductType', 'dayofweek']
    ).size().reset_index(name='count')

    print(f"🔍 Testing {len(recent_routes)} routes across 13 forecasting models...")
    print(f"   Total forecasts: {len(recent_routes) * 13:,}\n")

    all_forecasts = []

    for idx, row in recent_routes.iterrows():
        odc = row['ODC']
        ddc = row['DDC']
        product = row['ProductType']
        dow = row['dayofweek']

        # Get route history
        route_data = df[
            (df['ODC'] == odc) &
            (df['DDC'] == ddc) &
            (df['ProductType'] == product) &
            (df['dayofweek'] == dow)
        ].sort_values('date', ascending=False).copy()

        if len(route_data) == 0:
            continue

        # Run all models for this route
        model_forecasts = run_all_models_for_route(route_data, target_week, target_year, product)

        # Store results
        for model_name, forecast in model_forecasts.items():
            all_forecasts.append({
                'ODC': odc,
                'DDC': ddc,
                'ProductType': product,
                'dayofweek': dow,
                'model': model_name,
                'forecast': forecast,
                'week': target_week,
                'year': target_year
            })

        # Progress
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(recent_routes)} routes...")

    forecast_df = pd.DataFrame(all_forecasts)

    print(f"\n✅ Multi-Model Forecasts Generated:")
    print(f"   Total forecast records: {len(forecast_df):,}")
    print(f"   Unique routes: {len(recent_routes):,}")
    print(f"   Models tested: 13")

    return forecast_df

def compare_to_actuals_and_select_best(forecasts_df, actuals_path):
    """
    Compare all model forecasts to actuals and select best model per route.
    """
    print(f"\n{'='*80}")
    print("COMPARING TO ACTUALS & SELECTING BEST MODEL PER ROUTE")
    print(f"{'='*80}\n")

    # Load actuals
    actuals = pd.read_csv(actuals_path)
    actuals.columns = actuals.columns.str.strip()
    actuals['ProductType'] = actuals['Product Type']
    actuals['dayofweek'] = actuals['Day Index']

    # Create route keys
    forecasts_df['route_key'] = (
        forecasts_df['ODC'] + '|' +
        forecasts_df['DDC'] + '|' +
        forecasts_df['ProductType'] + '|' +
        forecasts_df['dayofweek'].astype(str)
    )

    actuals['route_key'] = (
        actuals['ODC'] + '|' +
        actuals['DDC'] + '|' +
        actuals['ProductType'] + '|' +
        actuals['dayofweek'].astype(str)
    )

    # Aggregate actuals by route
    actuals_agg = actuals.groupby('route_key').agg({
        'PIECES': 'sum',
        'ODC': 'first',
        'DDC': 'first',
        'ProductType': 'first'
    }).reset_index()

    print(f"📊 Loaded {len(actuals_agg)} actual routes")

    # Compare each model forecast to actuals
    results = []
    best_models_per_route = {}

    for route_key in forecasts_df['route_key'].unique():
        # Get all model forecasts for this route
        route_forecasts = forecasts_df[forecasts_df['route_key'] == route_key]

        # Get actual for this route
        actual_row = actuals_agg[actuals_agg['route_key'] == route_key]

        if len(actual_row) == 0:
            # Route was forecasted but didn't actually ship (ghost route)
            actual_value = 0
        else:
            actual_value = actual_row['PIECES'].values[0]

        # Calculate error for each model
        route_info = route_forecasts.iloc[0]
        best_model = None
        best_error = float('inf')

        for _, forecast_row in route_forecasts.iterrows():
            model = forecast_row['model']
            forecast = forecast_row['forecast']

            # Calculate absolute error
            error = abs(forecast - actual_value)
            pct_error = (error / actual_value * 100) if actual_value > 0 else (999 if forecast > 0 else 0)

            results.append({
                'route_key': route_key,
                'ODC': route_info['ODC'],
                'DDC': route_info['DDC'],
                'ProductType': route_info['ProductType'],
                'dayofweek': route_info['dayofweek'],
                'model': model,
                'forecast': forecast,
                'actual': actual_value,
                'abs_error': error,
                'pct_error': pct_error
            })

            # Track best model for this route
            if error < best_error:
                best_error = error
                best_model = model

        # Store best model for this route
        best_models_per_route[route_key] = {
            'ODC': route_info['ODC'],
            'DDC': route_info['DDC'],
            'ProductType': route_info['ProductType'],
            'dayofweek': route_info['dayofweek'],
            'best_model': best_model,
            'best_error': best_error,
            'actual': actual_value
        }

    results_df = pd.DataFrame(results)
    best_models_df = pd.DataFrame([
        {**{'route_key': k}, **v}
        for k, v in best_models_per_route.items()
    ])

    print(f"✅ Analyzed {len(best_models_per_route)} routes")

    return results_df, best_models_df

def analyze_results(results_df, best_models_df):
    """Generate analysis of which models won."""
    print(f"\n{'='*80}")
    print("ANALYSIS: WHICH MODELS WON?")
    print(f"{'='*80}\n")

    # Count winners
    model_wins = best_models_df['best_model'].value_counts()

    print(f"📊 MODEL PERFORMANCE (Routes Won):\n")
    for model, count in model_wins.items():
        pct = count / len(best_models_df) * 100
        print(f"   {model:<35} {count:>5} routes ({pct:>5.1f}%)")

    # Overall accuracy by model (across all routes)
    print(f"\n📈 AVERAGE ERROR BY MODEL (All Routes):\n")
    model_errors = results_df.groupby('model').agg({
        'abs_error': 'mean',
        'pct_error': 'mean'
    }).sort_values('abs_error')

    for model, row in model_errors.iterrows():
        print(f"   {model:<35} Avg Error: {row['abs_error']:>6.1f} pieces, MAPE: {row['pct_error']:>6.1f}%")

    # Which model would be best if we used it for ALL routes?
    print(f"\n🏆 IF WE USED ONE MODEL FOR ALL ROUTES:\n")
    for model in results_df['model'].unique():
        model_data = results_df[results_df['model'] == model]
        total_forecast = model_data['forecast'].sum()
        total_actual = model_data['actual'].sum()
        volume_error = abs(total_forecast - total_actual) / total_actual * 100 if total_actual > 0 else 999

        print(f"   {model:<35} Volume Error: {volume_error:>6.1f}%")

    return model_wins, model_errors

def save_results(results_df, best_models_df, model_wins, output_dir='.'):
    """Save all results to files."""
    output_dir = Path(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save detailed results
    results_path = output_dir / f"multi_model_results_{timestamp}.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\n💾 Detailed results saved to: {results_path}")

    # Save best model per route (routing table)
    routing_path = output_dir / f"route_model_routing_{timestamp}.csv"
    best_models_df.to_csv(routing_path, index=False)
    print(f"💾 Route→Model routing table saved to: {routing_path}")

    # Save summary
    summary_path = output_dir / f"model_performance_summary_{timestamp}.json"
    summary = {
        'timestamp': timestamp,
        'total_routes': len(best_models_df),
        'model_wins': model_wins.to_dict(),
        'total_models_tested': len(results_df['model'].unique())
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Performance summary saved to: {summary_path}")

    return routing_path

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Model Backtesting: Find best model per route"
    )
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--actuals', type=str, required=True, help='Path to actuals CSV')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"MULTI-MODEL BACKTESTING FRAMEWORK")
    print(f"Test ALL models on ALL routes, select winners")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        # Step 1: Generate forecasts with all models
        forecasts_df = generate_multi_model_forecasts(
            conn, args.week, args.year, args.table
        )

        # Step 2: Compare to actuals and select best model per route
        results_df, best_models_df = compare_to_actuals_and_select_best(
            forecasts_df, args.actuals
        )

        # Step 3: Analyze results
        model_wins, model_errors = analyze_results(results_df, best_models_df)

        # Step 4: Save results
        routing_path = save_results(results_df, best_models_df, model_wins)

        print(f"\n{'='*80}")
        print(f"✅ MULTI-MODEL BACKTESTING COMPLETE!")
        print(f"{'='*80}")
        print(f"\n📌 Next Steps:")
        print(f"   1. Review routing table: {routing_path}")
        print(f"   2. Use this to forecast future weeks")
        print(f"   3. Update routing table as new actuals come in")
        print(f"\n")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
