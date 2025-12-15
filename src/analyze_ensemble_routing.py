#!/usr/bin/env python3
"""
ENSEMBLE ROUTING ANALYSIS
Analyze performance when using the best model for each route (ensemble approach)
vs using a single model for all routes.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_ensemble_performance(filepath):
    """Analyze ensemble routing performance."""

    print("=" * 80)
    print("ENSEMBLE ROUTING ANALYSIS")
    print("=" * 80)

    # Load data
    df = pd.read_csv(filepath)

    # Filter routes with actuals
    routes_with_actuals = df[df['Actual'] > 0].copy()
    total_routes = len(routes_with_actuals)
    total_actual = routes_with_actuals['Actual'].sum()

    print(f"\n📊 Dataset: {total_routes:,} routes with actual data")
    print(f"📦 Total Actual Volume: {total_actual:,.0f} pieces")

    # === ENSEMBLE APPROACH (Best model per route) ===
    ensemble_errors = routes_with_actuals['Winner_Error%'].abs()
    ensemble_avg_mape = ensemble_errors.mean()
    ensemble_median_mape = ensemble_errors.median()
    ensemble_under_20pct = (ensemble_errors < 20).sum()
    ensemble_under_50pct = (ensemble_errors < 50).sum()

    print("\n" + "=" * 80)
    print("🎯 ENSEMBLE APPROACH (Best Model Per Route)")
    print("=" * 80)
    print(f"Average MAPE:          {ensemble_avg_mape:.1f}%")
    print(f"Median MAPE:           {ensemble_median_mape:.1f}%")
    print(f"Routes < 20% error:    {ensemble_under_20pct:,} ({ensemble_under_20pct/total_routes*100:.1f}%)")
    print(f"Routes < 50% error:    {ensemble_under_50pct:,} ({ensemble_under_50pct/total_routes*100:.1f}%)")

    # === SINGLE MODEL APPROACHES ===
    print("\n" + "=" * 80)
    print("📊 COMPARISON: Single Model for All Routes")
    print("=" * 80)

    # Get all model columns
    error_cols = [col for col in df.columns if col.endswith('_Error%') and col != 'Winner_Error%']

    single_model_results = []

    for error_col in error_cols:
        model_name = error_col.replace('_Error%', '')
        model_errors = routes_with_actuals[error_col].abs()
        avg_mape = model_errors.mean()
        median_mape = model_errors.median()
        under_20pct = (model_errors < 20).sum()
        under_50pct = (model_errors < 50).sum()

        single_model_results.append({
            'Model': model_name,
            'Avg_MAPE': avg_mape,
            'Median_MAPE': median_mape,
            'Routes_Under_20pct': under_20pct,
            'Routes_Under_50pct': under_50pct,
            'Improvement_vs_Ensemble': avg_mape - ensemble_avg_mape
        })

    results_df = pd.DataFrame(single_model_results).sort_values('Avg_MAPE')

    # Show top 10 single models
    print(f"\n{'Model':<40} {'Avg MAPE':<12} {'vs Ensemble':<15} {'<20% Error':<12}")
    print("-" * 80)

    for idx, row in results_df.head(10).iterrows():
        improvement = row['Improvement_vs_Ensemble']
        symbol = "📈" if improvement > 0 else "📉"
        print(f"{row['Model']:<40} {row['Avg_MAPE']:>6.1f}%      {symbol} {improvement:+6.1f}%      {row['Routes_Under_20pct']:>4} ({row['Routes_Under_20pct']/total_routes*100:>4.1f}%)")

    # Best single model
    best_single = results_df.iloc[0]

    print("\n" + "=" * 80)
    print("💡 KEY INSIGHTS")
    print("=" * 80)
    print(f"\n✅ ENSEMBLE APPROACH:")
    print(f"   Using best model per route: {ensemble_avg_mape:.1f}% average MAPE")
    print(f"\n❌ BEST SINGLE MODEL:")
    print(f"   Using {best_single['Model']} for all routes: {best_single['Avg_MAPE']:.1f}% average MAPE")
    print(f"\n🎯 IMPROVEMENT:")
    print(f"   Ensemble is {best_single['Improvement_vs_Ensemble']:.1f}% better than best single model")
    print(f"   That's a {best_single['Improvement_vs_Ensemble']/best_single['Avg_MAPE']*100:.1f}% relative improvement!")

    # Model distribution in ensemble
    print("\n" + "=" * 80)
    print("🔀 MODEL DISTRIBUTION IN ENSEMBLE")
    print("=" * 80)
    print(f"\nWhich models are used most frequently in the optimal ensemble?\n")

    model_usage = routes_with_actuals['Winner_Model'].value_counts()
    print(f"{'Model':<40} {'Routes':<10} {'%':<10}")
    print("-" * 80)
    for model, count in model_usage.head(15).items():
        print(f"{model:<40} {count:>6}     {count/total_routes*100:>5.1f}%")

    return {
        'ensemble_mape': ensemble_avg_mape,
        'best_single_mape': best_single['Avg_MAPE'],
        'improvement': best_single['Improvement_vs_Ensemble'],
        'results_df': results_df
    }

def create_routing_table(filepath, output_path='route_model_routing_table.csv'):
    """Create deployment-ready routing table."""

    print("\n" + "=" * 80)
    print("📋 CREATING ROUTING TABLE FOR DEPLOYMENT")
    print("=" * 80)

    df = pd.read_csv(filepath)

    # Create routing table
    routing_table = df[['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Winner_Model', 'Winner_Error%']].copy()
    routing_table = routing_table.rename(columns={
        'Winner_Model': 'Optimal_Model',
        'Winner_Error%': 'Historical_Error_Pct'
    })

    # Add confidence level based on error
    def confidence_level(error):
        abs_error = abs(error)
        if abs_error < 20:
            return 'HIGH'
        elif abs_error < 50:
            return 'MEDIUM'
        else:
            return 'LOW'

    routing_table['Confidence'] = routing_table['Historical_Error_Pct'].apply(confidence_level)

    # Save
    routing_table.to_csv(output_path, index=False)

    print(f"\n✅ Routing table saved: {output_path}")
    print(f"   Total routes: {len(routing_table):,}")
    print(f"\n   Columns:")
    print(f"   - route_key: Unique route identifier")
    print(f"   - ODC, DDC, ProductType, dayofweek: Route characteristics")
    print(f"   - Optimal_Model: Which forecasting model to use")
    print(f"   - Historical_Error_Pct: Historical error for this model on this route")
    print(f"   - Confidence: HIGH (<20% error), MEDIUM (20-50%), LOW (>50%)")

    # Confidence distribution
    confidence_dist = routing_table['Confidence'].value_counts()
    print(f"\n   Confidence Distribution:")
    for conf, count in confidence_dist.items():
        print(f"   - {conf}: {count:,} routes ({count/len(routing_table)*100:.1f}%)")

    return routing_table

def create_deployment_summary(routing_table, stats, output_path='deployment_summary.txt'):
    """Create deployment summary document."""

    print("\n" + "=" * 80)
    print("📄 CREATING DEPLOYMENT SUMMARY")
    print("=" * 80)

    lines = []
    lines.append("=" * 80)
    lines.append("FORECASTING MODEL ENSEMBLE - DEPLOYMENT SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    lines.append("")
    lines.append("This deployment uses an ENSEMBLE APPROACH where each route is forecasted")
    lines.append("using its optimal model (the model with lowest historical error for that route).")
    lines.append("")
    lines.append(f"Performance Metrics:")
    lines.append(f"  • Ensemble Average MAPE: {stats['ensemble_mape']:.1f}%")
    lines.append(f"  • Best Single Model MAPE: {stats['best_single_mape']:.1f}%")
    lines.append(f"  • Improvement: {stats['improvement']:.1f}% better than best single model")
    lines.append(f"  • Relative Improvement: {stats['improvement']/stats['best_single_mape']*100:.1f}%")
    lines.append("")
    lines.append("-" * 80)
    lines.append("DEPLOYMENT INSTRUCTIONS")
    lines.append("-" * 80)
    lines.append("")
    lines.append("1. Load the routing table: route_model_routing_table.csv")
    lines.append("")
    lines.append("2. For each route to forecast:")
    lines.append("   a. Look up route in routing table by:")
    lines.append("      - route_key (exact match)")
    lines.append("      OR")
    lines.append("      - ODC + DDC + ProductType + dayofweek")
    lines.append("")
    lines.append("   b. Use the 'Optimal_Model' specified for that route")
    lines.append("")
    lines.append("   c. Check 'Confidence' level:")
    lines.append("      - HIGH: Error typically < 20%")
    lines.append("      - MEDIUM: Error typically 20-50%")
    lines.append("      - LOW: Error typically > 50% (use with caution)")
    lines.append("")
    lines.append("3. If route not found in routing table:")
    lines.append(f"   - Use default model: {stats['results_df'].iloc[0]['Model']}")
    lines.append(f"   - This is the best performing single model overall")
    lines.append("")
    lines.append("-" * 80)
    lines.append("MODELS IN ENSEMBLE")
    lines.append("-" * 80)
    lines.append("")

    model_usage = routing_table['Optimal_Model'].value_counts()
    for model, count in model_usage.items():
        lines.append(f"{model:<40} {count:>6} routes")

    lines.append("")
    lines.append("=" * 80)

    summary_text = '\n'.join(lines)

    with open(output_path, 'w') as f:
        f.write(summary_text)

    print(f"\n✅ Deployment summary saved: {output_path}")
    print("\n" + summary_text)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Ensemble Routing Performance")
    parser.add_argument('--input', type=str, required=True, help='Path to comprehensive comparison CSV')
    parser.add_argument('--routing-table', type=str, default='route_model_routing_table.csv', help='Output routing table path')
    parser.add_argument('--summary', type=str, default='deployment_summary.txt', help='Output summary path')
    args = parser.parse_args()

    # Analyze performance
    stats = analyze_ensemble_performance(args.input)

    # Create routing table
    routing_table = create_routing_table(args.input, args.routing_table)

    # Create deployment summary
    create_deployment_summary(routing_table, stats, args.summary)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  1. {args.routing_table} - Route-to-model routing table")
    print(f"  2. {args.summary} - Deployment summary document")

if __name__ == "__main__":
    main()
