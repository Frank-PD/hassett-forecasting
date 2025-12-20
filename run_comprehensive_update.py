#!/usr/bin/env python3
"""
Comprehensive Weekly Forecast Update - Full Run (All 18 Models)
Executes all steps from the notebook in a single script
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from databricks import sql
import json
import warnings
warnings.filterwarnings('ignore')

# Progress bars
from tqdm.auto import tqdm

# Add src to path
project_root = Path.cwd()
sys.path.insert(0, str(project_root / 'src'))

# Import model functions
from forecast_comprehensive_all_models import ComprehensiveModels
from performance_tracker import PerformanceTracker

def load_previous_model_performance(project_root):
    """Load most recent performance summary to identify underperforming models"""
    json_files = sorted(project_root.glob('model_performance_summary_*.json'))

    if len(json_files) == 0:
        return None

    # Get most recent file
    latest_file = json_files[-1]
    with open(latest_file, 'r') as f:
        data = json.load(f)

    return data.get('model_wins', {})

def main():
    # Configuration
    AUTO_PRUNE_ZERO_WIN_MODELS = True  # Set to False to disable automatic pruning

    print("="*80)
    print("COMPREHENSIVE WEEKLY FORECAST UPDATE - OPTIMIZED (14 MODELS)")
    print("="*80)
    print("\n✅ Setup complete!\n")

    # Auto-calculate weeks
    today = datetime.now()
    current_week = today.isocalendar()[1]
    current_year = today.year

    EVALUATION_WEEK = current_week - 1
    FORECAST_WEEK = current_week

    if EVALUATION_WEEK < 1:
        EVALUATION_WEEK = 52
        EVALUATION_YEAR = current_year - 1
        FORECAST_YEAR = current_year
    else:
        EVALUATION_YEAR = current_year
        FORECAST_YEAR = current_year

    # Config
    DATABRICKS_CONFIG = {
        "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
        "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
        "auth_type": "databricks-oauth"
    }

    TABLE_NAME = "decus_domesticops_prod.dbo.tmp_hassett_report"
    TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

    print(f"📋 Auto-Configuration (Today: {today.strftime('%Y-%m-%d')}):")
    print(f"  Current Week: {current_week}")
    print(f"  Evaluation Week: {EVALUATION_WEEK}, {EVALUATION_YEAR} (last week - has actuals)")
    print(f"  Forecast Week: {FORECAST_WEEK}, {FORECAST_YEAR} (current week)")
    print(f"  Timestamp: {TIMESTAMP}")
    print()

    # Connect to Databricks
    print("🔌 Connecting to Databricks...")
    conn = sql.connect(**DATABRICKS_CONFIG)
    print("✅ Connected!\n")

    # Step 1: Load historical data
    print(f"📊 Step 1: Loading historical data (4 years)...")
    year_start = datetime(EVALUATION_YEAR, 1, 1)
    target_date = year_start + timedelta(weeks=EVALUATION_WEEK - 1)
    lookback_date = target_date - timedelta(days=365 * 4)

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
    df_historical = pd.DataFrame(rows, columns=columns)
    df_historical['date'] = pd.to_datetime(df_historical['date'])
    print(f"✅ Loaded {len(df_historical):,} historical records\n")

    # Step 2: Get actuals
    print(f"📊 Step 2: Getting actuals for week {EVALUATION_WEEK}, {EVALUATION_YEAR}...")
    query_actuals = f"""
    SELECT
        ODC,
        DDC,
        ProductType,
        dayofweek(DATE_SHIP) as dayofweek,
        SUM(PIECES) as actual_pieces
    FROM {TABLE_NAME}
    WHERE weekofyear(DATE_SHIP) = {EVALUATION_WEEK}
        AND YEAR(DATE_SHIP) = {EVALUATION_YEAR}
        AND ProductType IN ('MAX', 'EXP')
    GROUP BY ODC, DDC, ProductType, dayofweek(DATE_SHIP)
    ORDER BY ODC, DDC, ProductType, dayofweek
    """

    cursor.execute(query_actuals)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df_actuals = pd.DataFrame(rows, columns=columns)
    print(f"✅ Found {len(df_actuals):,} route-day actuals")
    print(f"   Total pieces: {df_actuals['actual_pieces'].sum():,.0f}\n")

    # Step 3: Generate forecasts with optimized model set
    routes = df_actuals[['ODC', 'DDC', 'ProductType', 'dayofweek']].drop_duplicates()

    # OPTIMIZED MODEL SET (Removed models 15-18: 0 wins, never competitive)
    # Based on meta-analysis: models 15-18 had 0 wins across all evaluations
    all_model_functions = [
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

    # AUTOMATED MODEL PRUNING: Remove models with 0 wins in previous run
    pruned_models = []
    if AUTO_PRUNE_ZERO_WIN_MODELS:
        previous_performance = load_previous_model_performance(project_root)
        if previous_performance:
            # Filter out models with 0 wins
            model_functions = []
            for name, func in all_model_functions:
                # Normalize name to match previous performance data
                if name in previous_performance or previous_performance.get(name, 1) > 0:
                    model_functions.append((name, func))
                else:
                    pruned_models.append(name)

            if pruned_models:
                print(f"🔧 AUTO-PRUNING: Removed {len(pruned_models)} models with 0 wins in previous run:")
                for model in pruned_models:
                    print(f"   ❌ {model}")
                print()
        else:
            model_functions = all_model_functions
            print("ℹ️  No previous performance data found - using all 14 models\n")
    else:
        model_functions = all_model_functions

    print(f"📊 Step 3: Generating forecasts for {len(routes):,} route-days using {len(model_functions)} MODELS...")
    if len(pruned_models) > 0:
        print(f"   (Auto-pruned {len(pruned_models)} zero-win models)")
    print(f"⏱️  Estimated time: {20 + len(model_functions) * 1.5:.0f}-{30 + len(model_functions) * 2:.0f} minutes\n")

    results = []
    pbar = tqdm(routes.iterrows(), total=len(routes), desc="Evaluating 14 optimized models")

    for idx, route in pbar:
        odc, ddc, product, dow = route['ODC'], route['DDC'], route['ProductType'], route['dayofweek']
        pbar.set_postfix({'Route': f"{odc}-{ddc}-{product}"})

        route_data = df_historical[
            (df_historical['ODC'] == odc) &
            (df_historical['DDC'] == ddc) &
            (df_historical['ProductType'] == product) &
            (df_historical['dayofweek'] == dow)
        ].sort_values('date', ascending=False)

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

        for model_name, model_func in model_functions:
            try:
                forecast = model_func(route_data, EVALUATION_WEEK, EVALUATION_YEAR, product)
                result[model_name] = max(0, forecast)
            except Exception as e:
                result[model_name] = 0

        results.append(result)

    df_forecasts = pd.DataFrame(results)
    print(f"\n✅ Generated forecasts for {len(df_forecasts):,} routes using all 18 models\n")

    # Step 4: Calculate errors
    print(f"📊 Step 4: Calculating errors...")
    model_cols = [col for col in df_forecasts.columns if col not in ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual']]

    for col in model_cols:
        error_col = f"{col}_Error%"
        df_forecasts[error_col] = np.where(
            df_forecasts['Actual'] > 0,
            abs((df_forecasts[col] - df_forecasts['Actual']) / df_forecasts['Actual'] * 100),
            np.where(df_forecasts[col] > 0, 999, 0)
        )

    error_cols = [col for col in df_forecasts.columns if col.endswith('_Error%')]
    df_forecasts['Winner_Model'] = df_forecasts[error_cols].abs().idxmin(axis=1).str.replace('_Error%', '')
    df_forecasts['Winner_Error%'] = df_forecasts[error_cols].abs().min(axis=1)

    print(f"✅ Winners determined!\n")
    print(f"🏆 Model Win Summary (Top 10):")
    win_summary = df_forecasts['Winner_Model'].value_counts()
    for i, (model, count) in enumerate(win_summary.head(10).items(), 1):
        pct = count / len(df_forecasts) * 100
        print(f"  {i:2}. {model:<30} {count:4,} routes ({pct:5.1f}%)")
    print()

    # Step 4b: Record performance to tracking database (WEEKLY UPDATE)
    print(f"📊 Step 4b: Recording performance to tracking database...")
    db_path = project_root / 'data' / 'performance' / 'performance_tracking.db'
    tracker = PerformanceTracker(str(db_path))

    # Prepare data for recording - need route info + all model forecasts + actual
    week_results = df_forecasts.copy()
    week_results['week_number'] = EVALUATION_WEEK
    week_results['year'] = EVALUATION_YEAR
    week_results['actual_value'] = week_results['Actual']

    tracker.record_week_performance(week_results)
    print(f"✅ Performance recorded to {db_path.name}\n")

    # Step 5: Save files (organized in data/ folder)
    print(f"📊 Step 5: Saving files...")

    # Create output directories if they don't exist
    (project_root / 'data' / 'comprehensive').mkdir(parents=True, exist_ok=True)
    (project_root / 'data' / 'routing_tables').mkdir(parents=True, exist_ok=True)
    (project_root / 'data' / 'performance').mkdir(parents=True, exist_ok=True)

    # Save comprehensive comparison
    output_file = project_root / 'data' / 'comprehensive' / f'comprehensive_all_models_week{EVALUATION_WEEK}.csv'
    df_forecasts.to_csv(output_file, index=False)
    print(f"💾 Saved: data/comprehensive/{output_file.name}")

    routing_table = df_forecasts[[
        'route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek',
        'Winner_Model', 'Winner_Error%', 'Actual'
    ]].copy()
    routing_table.columns = ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'best_model', 'best_error', 'actual']

    def assign_confidence(error):
        if error == 999:
            return 'LOW'
        elif error <= 20:
            return 'HIGH'
        elif error <= 50:
            return 'MEDIUM'
        else:
            return 'LOW'

    routing_table['confidence'] = routing_table['best_error'].apply(assign_confidence)

    # Save timestamped routing table
    routing_file = project_root / 'data' / 'routing_tables' / f'route_model_routing_{TIMESTAMP}.csv'
    routing_table.to_csv(routing_file, index=False)
    print(f"💾 Saved: data/routing_tables/{routing_file.name}")

    # Update current routing table (always latest)
    current_routing_file = project_root / 'data' / 'routing_tables' / 'route_model_routing_table.csv'
    routing_table.to_csv(current_routing_file, index=False)
    print(f"💾 Updated: data/routing_tables/{current_routing_file.name}")

    # Step 5b: Update routing table based on rolling 4-week performance
    print(f"\n📊 Step 5b: Updating routing table based on rolling 4-week performance...")

    # Load current routing table for update
    routing_for_update = routing_table.copy()
    routing_for_update.rename(columns={'best_model': 'Optimal_Model', 'best_error': 'Historical_Error_Pct'}, inplace=True)

    # Update based on rolling performance (4 weeks lookback, min 2 weeks data)
    updated_routing = tracker.update_routing_table(routing_for_update, lookback_weeks=4, min_weeks=2)

    # Save updated routing table
    updated_routing.rename(columns={'Optimal_Model': 'best_model', 'Historical_Error_Pct': 'best_error'}, inplace=True)
    updated_routing.to_csv(current_routing_file, index=False)
    print(f"💾 Updated routing table with rolling performance: {current_routing_file.name}")

    # Reload for forecast generation
    routing_table = updated_routing.copy()
    routing_table.rename(columns={'best_model': 'best_model', 'best_error': 'best_error'}, inplace=True)

    # Save performance summary
    performance_summary = {
        'timestamp': TIMESTAMP,
        'evaluation_week': EVALUATION_WEEK,
        'evaluation_year': EVALUATION_YEAR,
        'total_routes': len(df_forecasts),
        'total_actuals': int(df_forecasts['Actual'].sum()),
        'model_wins': {str(k): int(v) for k, v in win_summary.to_dict().items()}
    }

    perf_file = project_root / 'data' / 'performance' / f'model_performance_summary_{TIMESTAMP}.json'
    with open(perf_file, 'w') as f:
        json.dump(performance_summary, f, indent=2)
    print(f"💾 Saved: data/performance/{perf_file.name}\n")

    # Step 6: Generate forecast for next week
    print(f"📊 Step 6: Generating forecast for week {FORECAST_WEEK}...")

    # Load historical data for forecast week
    year_start = datetime(FORECAST_YEAR, 1, 1)
    target_date_forecast = year_start + timedelta(weeks=FORECAST_WEEK - 1)
    lookback_date_forecast = target_date_forecast - timedelta(days=365 * 4)

    query_forecast = f"""
    SELECT
        DATE_SHIP as date,
        ODC, DDC, ProductType,
        PIECES as pieces,
        weekofyear(DATE_SHIP) as week,
        YEAR(DATE_SHIP) as year,
        dayofweek(DATE_SHIP) as dayofweek
    FROM {TABLE_NAME}
    WHERE DATE_SHIP >= '{lookback_date_forecast.strftime('%Y-%m-%d')}'
        AND DATE_SHIP < '{target_date_forecast.strftime('%Y-%m-%d')}'
        AND ProductType IN ('MAX', 'EXP')
        AND ODC IS NOT NULL
        AND DDC IS NOT NULL
    ORDER BY DATE_SHIP DESC
    """

    cursor.execute(query_forecast)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df_historical_forecast = pd.DataFrame(rows, columns=columns)
    df_historical_forecast['date'] = pd.to_datetime(df_historical_forecast['date'])

    forecast_results = []
    ensemble_count = 0
    pbar = tqdm(routing_table.iterrows(), total=len(routing_table), desc="Generating forecasts")

    for idx, route in pbar:
        odc, ddc, product, dow = route['ODC'], route['DDC'], route['ProductType'], route['dayofweek']
        best_model = route['best_model']
        confidence = route['confidence']

        route_data = df_historical_forecast[
            (df_historical_forecast['ODC'] == odc) &
            (df_historical_forecast['DDC'] == ddc) &
            (df_historical_forecast['ProductType'] == product) &
            (df_historical_forecast['dayofweek'] == dow)
        ].sort_values('date', ascending=False)

        # CONFIDENCE-BASED ENSEMBLE: Use top 3 models for LOW confidence routes
        if confidence == 'LOW':
            # Get top 3 models from comprehensive forecast
            route_key = route['route_key']
            comprehensive_row = df_forecasts[df_forecasts['route_key'] == route_key]

            if len(comprehensive_row) > 0:
                # Get all error columns
                error_cols = [col for col in df_forecasts.columns if col.endswith('_Error%')]
                errors = comprehensive_row[error_cols].iloc[0]

                # Get top 3 models with lowest errors
                top_3_models = errors.nsmallest(3).index.str.replace('_Error%', '').tolist()

                # Generate forecasts from top 3 and blend
                forecasts = []
                for model_name in top_3_models:
                    model_func = None
                    for name, func in model_functions:
                        if name == model_name:
                            model_func = func
                            break

                    if model_func:
                        try:
                            f = model_func(route_data, FORECAST_WEEK, FORECAST_YEAR, product)
                            forecasts.append(max(0, f))
                        except:
                            pass

                # Ensemble: average of top 3
                if forecasts:
                    forecast = sum(forecasts) / len(forecasts)
                    optimal_model = f"ENSEMBLE_{len(forecasts)}"
                    ensemble_count += 1
                else:
                    forecast = 0
                    optimal_model = best_model
            else:
                forecast = 0
                optimal_model = best_model
        else:
            # HIGH/MEDIUM confidence: use single best model
            model_func = None
            for name, func in model_functions:
                if name == best_model:
                    model_func = func
                    break

            if model_func is None:
                forecast = 0
            else:
                try:
                    forecast = model_func(route_data, FORECAST_WEEK, FORECAST_YEAR, product)
                    forecast = max(0, forecast)
                except:
                    forecast = 0

            optimal_model = best_model

        variance_pct = 50.0
        variance_pieces = forecast * (variance_pct / 100)

        forecast_results.append({
            'route_key': route['route_key'],
            'ODC': odc,
            'DDC': ddc,
            'ProductType': product,
            'dayofweek': dow,
            'week_number': FORECAST_WEEK,
            'year': FORECAST_YEAR,
            'forecast': forecast,
            'optimal_model': optimal_model,
            'confidence': route['confidence'],
            'historical_error_pct': route['best_error'],
            'forecast_low': max(0, forecast - variance_pieces),
            'forecast_high': forecast + variance_pieces,
            'variance_pieces': variance_pieces,
            'variance_pct': variance_pct
        })

    df_production_forecast = pd.DataFrame(forecast_results)

    # Create forecasts directory if it doesn't exist
    (project_root / 'data' / 'forecasts').mkdir(parents=True, exist_ok=True)

    # Save production forecast
    prod_forecast_file = project_root / 'data' / 'forecasts' / f'production_forecast_week{FORECAST_WEEK}.csv'
    df_production_forecast.to_csv(prod_forecast_file, index=False)
    print(f"\n💾 Saved: data/forecasts/{prod_forecast_file.name}")
    print(f"   📊 Ensemble forecasts used for {ensemble_count} LOW confidence routes\n")

    # Final summary
    print("="*80)
    print(f"COMPREHENSIVE WEEKLY UPDATE COMPLETE - {TIMESTAMP}")
    print("="*80)
    print(f"\n📊 Evaluation (Week {EVALUATION_WEEK}, {EVALUATION_YEAR}):")
    print(f"  • Routes evaluated: {len(df_forecasts):,}")
    print(f"  • Actual pieces: {df_actuals['actual_pieces'].sum():,.0f}")
    print(f"  • Models tested: {len(model_cols)}")

    print(f"\n📈 Forecast (Week {FORECAST_WEEK}, {FORECAST_YEAR}):")
    print(f"  • Routes forecasted: {len(df_production_forecast):,}")
    print(f"  • Total forecast: {df_production_forecast['forecast'].sum():,.0f} pieces")
    print(f"  • Ensemble forecasts: {ensemble_count} routes (LOW confidence)")

    by_confidence = df_production_forecast.groupby('confidence').size()
    print(f"\n  By Confidence Level:")
    for conf in ['HIGH', 'MEDIUM', 'LOW']:
        if conf in by_confidence.index:
            print(f"    • {conf}: {by_confidence[conf]:,} routes")

    by_product = df_production_forecast.groupby('ProductType')['forecast'].sum()
    print(f"\n  By Product Type:")
    for product, total in by_product.items():
        print(f"    • {product}: {total:,.0f} pieces")

    print(f"\n💾 Files Generated:")
    print(f"  • {output_file.name}")
    print(f"  • {routing_file.name}")
    print(f"  • {current_routing_file.name}")
    print(f"  • {perf_file.name}")
    print(f"  • {prod_forecast_file.name}")

    print(f"\n" + "="*80)
    print("✅ ALL UPDATES COMPLETE!")
    print("="*80)

    conn.close()
    tracker.close()
    print("\n🔌 Databricks connection closed")
    print("🔌 Performance tracker database closed")

    # Run meta-analysis to track model performance trends
    print("\n" + "="*80)
    print("📊 RUNNING META-ANALYSIS: Tracking Model Performance")
    print("="*80)
    print()

    try:
        import subprocess
        result = subprocess.run(
            ['python3', str(project_root / 'model_meta_analysis.py')],
            capture_output=True,
            text=True,
            timeout=60
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"⚠️  Meta-analysis warning: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not run meta-analysis: {e}")
        print("   Run 'python3 model_meta_analysis.py' manually to see model trends")

    print("\n" + "="*80)
    print("✅ ALL PROCESSES COMPLETE!")
    print("="*80)

if __name__ == "__main__":
    main()
