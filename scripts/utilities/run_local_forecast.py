#!/usr/bin/env python3
"""
LOCAL FORECAST RUNNER
Simulates Azure Data Factory pipeline locally for testing.

This script:
1. Loads the routing table
2. For each route to forecast, looks up the optimal model
3. Runs that specific model
4. Generates forecasts
5. Compares to actuals (if provided)
6. Shows performance metrics
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
from datetime import datetime

# Import the comprehensive models
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from forecast_comprehensive_all_models import ComprehensiveModels

class LocalForecastRunner:
    """Run forecasts locally using the routing table."""

    def __init__(self, routing_table_path, historical_data_path):
        """Initialize with routing table and historical data."""

        print("=" * 80)
        print("LOCAL FORECAST RUNNER")
        print("=" * 80)

        # Load routing table
        print(f"\n📂 Loading routing table: {routing_table_path}")
        self.routing_table = pd.read_csv(routing_table_path)
        print(f"   ✅ Loaded {len(self.routing_table):,} routes")

        # Load historical data
        print(f"\n📂 Loading historical data: {historical_data_path}")
        self.historical_data = pd.read_csv(historical_data_path)

        # Standardize column names
        self.historical_data.columns = [
            'week_ending' if 'week' in col.lower() and 'ending' in col.lower() else
            'ProductType' if 'product' in col.lower() and 'type' in col.lower() else
            'ODC' if col == 'ODC' else
            'DDC' if col == 'DDC' else
            'pieces' if 'piece' in col.lower() else
            'dayofweek' if 'day' in col.lower() and 'index' in col.lower() else
            col for col in self.historical_data.columns
        ]

        print(f"   ✅ Loaded {len(self.historical_data):,} historical records")

        # Parse week_ending date
        self.historical_data['week_ending'] = pd.to_datetime(self.historical_data['week_ending'])

        # Model statistics
        self.model_counts = self.routing_table['Optimal_Model'].value_counts()
        print(f"\n📊 Model Distribution in Routing Table:")
        for model, count in self.model_counts.head(10).items():
            print(f"   {model:<40} {count:>5} routes ({count/len(self.routing_table)*100:>5.1f}%)")

    def get_route_data(self, ODC, DDC, ProductType, dayofweek):
        """Get historical data for a specific route."""

        route_data = self.historical_data[
            (self.historical_data['ODC'] == ODC) &
            (self.historical_data['DDC'] == DDC) &
            (self.historical_data['ProductType'] == ProductType) &
            (self.historical_data['dayofweek'] == dayofweek)
        ].sort_values('week_ending', ascending=False)

        return route_data

    def run_model(self, model_name, route_data):
        """Run a specific forecasting model."""

        # Map model names to model functions
        model_mapping = {
            '01_Historical_Baseline': ComprehensiveModels.model_01_historical_baseline,
            '02_Recent_2W': ComprehensiveModels.model_02_recent_2w_avg,
            '03_Recent_4W_HYBRID': ComprehensiveModels.model_03_recent_4w_avg,
            '04_Recent_8W': ComprehensiveModels.model_04_recent_8w_avg,
            '05_Trend_Adjusted': ComprehensiveModels.model_05_trend_adjusted,
            '06_Prior_Week': ComprehensiveModels.model_06_prior_week,
            '07_Same_Week_Last_Year': ComprehensiveModels.model_07_same_week_last_year,
            '08_Week_Specific': ComprehensiveModels.model_08_week_specific_historical,
            '09_Exp_Smoothing': ComprehensiveModels.model_09_exponential_smoothing,
            '10_Probabilistic': ComprehensiveModels.model_10_probabilistic,
            '11_Hybrid_Week_Blend': ComprehensiveModels.model_11_hybrid_week_blend,
            '12_Median_Recent': ComprehensiveModels.model_12_median_recent,
            '13_Weighted_Recent_Week': ComprehensiveModels.model_13_weighted_recent_week,
            '14_SARIMA': ComprehensiveModels.model_14_sarima,
            '15_ML_Classifier_Simple_Vol': ComprehensiveModels.model_15_ml_classifier_simple_volume,
            '16_ML_Regressor': ComprehensiveModels.model_16_ml_regressor,
            '17_Lane_Adaptive': ComprehensiveModels.model_17_lane_adaptive,
            '18_Clustering': ComprehensiveModels.model_18_clustering,
        }

        if model_name not in model_mapping:
            # Default to historical baseline
            print(f"   ⚠️  Unknown model {model_name}, using Historical Baseline")
            model_name = '01_Historical_Baseline'

        model_func = model_mapping[model_name]

        # Run the model
        try:
            forecast = model_func(route_data)
            return forecast
        except Exception as e:
            print(f"   ⚠️  Error running {model_name}: {e}")
            # Fallback to simple average
            if len(route_data) > 0:
                return route_data['pieces'].mean()
            else:
                return 0

    def forecast_routes(self, routes_to_forecast, week_number=None, year=None):
        """
        Forecast a list of routes using their optimal models.

        Args:
            routes_to_forecast: DataFrame with columns [ODC, DDC, ProductType, dayofweek]
            week_number: Week number to forecast (optional)
            year: Year to forecast (optional)

        Returns:
            DataFrame with forecasts
        """

        print("\n" + "=" * 80)
        print("GENERATING FORECASTS")
        print("=" * 80)
        print(f"\n📊 Forecasting {len(routes_to_forecast):,} routes...")

        forecasts = []
        routes_processed = 0

        for idx, route in routes_to_forecast.iterrows():
            routes_processed += 1

            # Progress indicator
            if routes_processed % 50 == 0:
                print(f"   Progress: {routes_processed}/{len(routes_to_forecast)} routes...")

            # Create route key
            route_key = f"{route['ODC']}-{route['DDC']}-{route['ProductType']}-{route['dayofweek']}"

            # Look up optimal model in routing table
            routing_entry = self.routing_table[
                (self.routing_table['ODC'] == route['ODC']) &
                (self.routing_table['DDC'] == route['DDC']) &
                (self.routing_table['ProductType'] == route['ProductType']) &
                (self.routing_table['dayofweek'] == route['dayofweek'])
            ]

            if len(routing_entry) > 0:
                optimal_model = routing_entry.iloc[0]['Optimal_Model']
                confidence = routing_entry.iloc[0].get('Confidence', 'UNKNOWN')
                historical_error = routing_entry.iloc[0].get('Historical_Error_Pct', 0)
            else:
                # Route not in routing table, use default model
                optimal_model = '04_Recent_8W'  # Best single model
                confidence = 'NEW_ROUTE'
                historical_error = 0
                print(f"   ⚠️  Route {route_key} not in routing table, using default model")

            # Get historical data for this route
            route_data = self.get_route_data(
                route['ODC'],
                route['DDC'],
                route['ProductType'],
                route['dayofweek']
            )

            # Run the optimal model
            forecast_value = self.run_model(optimal_model, route_data)

            # Store forecast
            forecasts.append({
                'route_key': route_key,
                'ODC': route['ODC'],
                'DDC': route['DDC'],
                'ProductType': route['ProductType'],
                'dayofweek': route['dayofweek'],
                'week_number': week_number,
                'year': year,
                'optimal_model': optimal_model,
                'forecast': forecast_value,
                'confidence': confidence,
                'historical_error_pct': historical_error,
                'forecast_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        forecasts_df = pd.DataFrame(forecasts)

        print(f"\n✅ Generated {len(forecasts_df):,} forecasts")
        print(f"\n📊 Models Used:")
        model_usage = forecasts_df['optimal_model'].value_counts()
        for model, count in model_usage.head(10).items():
            print(f"   {model:<40} {count:>5} routes")

        return forecasts_df

    def compare_to_actuals(self, forecasts_df, actuals_df):
        """Compare forecasts to actual values."""

        print("\n" + "=" * 80)
        print("COMPARING TO ACTUALS")
        print("=" * 80)

        # Standardize actuals column names
        actuals_df.columns = [
            'week_ending' if 'week' in col.lower() and 'ending' in col.lower() else
            'ProductType' if 'product' in col.lower() and 'type' in col.lower() else
            'ODC' if col == 'ODC' else
            'DDC' if col == 'DDC' else
            'pieces' if 'piece' in col.lower() else
            'dayofweek' if 'day' in col.lower() and 'index' in col.lower() else
            col for col in actuals_df.columns
        ]

        # Merge forecasts with actuals
        comparison = forecasts_df.merge(
            actuals_df[['ODC', 'DDC', 'ProductType', 'dayofweek', 'pieces']],
            on=['ODC', 'DDC', 'ProductType', 'dayofweek'],
            how='left'
        )

        comparison = comparison.rename(columns={'pieces': 'actual'})

        # Calculate errors
        comparison['error_pct'] = ((comparison['forecast'] - comparison['actual']) / comparison['actual'] * 100).replace([np.inf, -np.inf], 0)
        comparison['absolute_error_pct'] = comparison['error_pct'].abs()

        # Filter to routes with actuals
        comparison_with_actuals = comparison[comparison['actual'].notna() & (comparison['actual'] > 0)].copy()

        if len(comparison_with_actuals) == 0:
            print("⚠️  No actuals found to compare against")
            return comparison

        print(f"\n📊 Comparison Results ({len(comparison_with_actuals):,} routes with actuals):")
        print(f"   Average MAPE: {comparison_with_actuals['absolute_error_pct'].mean():.1f}%")
        print(f"   Median MAPE: {comparison_with_actuals['absolute_error_pct'].median():.1f}%")
        print(f"   Routes <20% error: {(comparison_with_actuals['absolute_error_pct'] < 20).sum()} ({(comparison_with_actuals['absolute_error_pct'] < 20).sum() / len(comparison_with_actuals) * 100:.1f}%)")
        print(f"   Routes <50% error: {(comparison_with_actuals['absolute_error_pct'] < 50).sum()} ({(comparison_with_actuals['absolute_error_pct'] < 50).sum() / len(comparison_with_actuals) * 100:.1f}%)")

        # Performance by confidence level
        print(f"\n📊 Performance by Confidence Level:")
        for conf in ['HIGH', 'MEDIUM', 'LOW', 'NEW_ROUTE']:
            conf_routes = comparison_with_actuals[comparison_with_actuals['confidence'] == conf]
            if len(conf_routes) > 0:
                print(f"   {conf:<12} {len(conf_routes):>5} routes, Avg MAPE: {conf_routes['absolute_error_pct'].mean():>6.1f}%")

        # Performance by model
        print(f"\n📊 Performance by Model (Top 10):")
        model_performance = comparison_with_actuals.groupby('optimal_model').agg({
            'absolute_error_pct': 'mean',
            'route_key': 'count'
        }).sort_values('absolute_error_pct')

        for model, row in model_performance.head(10).iterrows():
            print(f"   {model:<40} {row['route_key']:>5} routes, Avg MAPE: {row['absolute_error_pct']:>6.1f}%")

        return comparison

def main():
    parser = argparse.ArgumentParser(description="Run Forecasts Locally Using Routing Table")
    parser.add_argument('--routing-table', type=str, default='route_model_routing_table.csv',
                       help='Path to routing table CSV')
    parser.add_argument('--historical-data', type=str, required=True,
                       help='Path to historical data CSV')
    parser.add_argument('--routes-to-forecast', type=str, required=True,
                       help='Path to CSV with routes to forecast (ODC, DDC, ProductType, dayofweek)')
    parser.add_argument('--actuals', type=str, help='Path to actuals CSV (optional, for validation)')
    parser.add_argument('--output', type=str, default='local_forecasts.csv',
                       help='Output path for forecasts')
    parser.add_argument('--week', type=int, help='Week number (optional)')
    parser.add_argument('--year', type=int, help='Year (optional)')
    args = parser.parse_args()

    # Initialize runner
    runner = LocalForecastRunner(args.routing_table, args.historical_data)

    # Load routes to forecast
    print(f"\n📂 Loading routes to forecast: {args.routes_to_forecast}")
    routes_to_forecast = pd.read_csv(args.routes_to_forecast)

    # Standardize column names
    routes_to_forecast.columns = [
        'ProductType' if 'product' in col.lower() and 'type' in col.lower() else
        'ODC' if col == 'ODC' else
        'DDC' if col == 'DDC' else
        'dayofweek' if 'day' in col.lower() else
        col for col in routes_to_forecast.columns
    ]

    print(f"   ✅ Loaded {len(routes_to_forecast):,} routes to forecast")

    # Generate forecasts
    forecasts_df = runner.forecast_routes(routes_to_forecast, args.week, args.year)

    # Compare to actuals if provided
    if args.actuals:
        print(f"\n📂 Loading actuals: {args.actuals}")
        actuals_df = pd.read_csv(args.actuals)
        forecasts_df = runner.compare_to_actuals(forecasts_df, actuals_df)

    # Save forecasts
    forecasts_df.to_csv(args.output, index=False)
    print(f"\n✅ Forecasts saved to: {args.output}")

    print("\n" + "=" * 80)
    print("✅ LOCAL FORECAST COMPLETE")
    print("=" * 80)

    print(f"\nGenerated files:")
    print(f"  {args.output} - Forecast results")

    if args.actuals:
        print(f"\n💡 Next Steps:")
        print(f"  1. Review forecast results in {args.output}")
        print(f"  2. Check that MAPE is close to 14.3% (ensemble target)")
        print(f"  3. If results look good, deploy to Azure Data Factory!")
    else:
        print(f"\n💡 To validate forecasts:")
        print(f"  Run again with --actuals flag when actual data is available")

if __name__ == "__main__":
    main()
