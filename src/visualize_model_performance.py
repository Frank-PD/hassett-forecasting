#!/usr/bin/env python3
"""
VISUALIZE MODEL PERFORMANCE
Create comprehensive visualizations of all model performance metrics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_comparison_data(filepath):
    """Load the comprehensive comparison file."""
    df = pd.read_csv(filepath)
    model_cols = [c for c in df.columns if not c.endswith('_Error%') and c not in ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual', 'Winner_Model', 'Winner_Error%']]
    print(f"✅ Loaded {len(df):,} routes with {len(model_cols)} models")
    return df

def plot_winner_distribution(df, output_dir='visualizations'):
    """Plot which models won most routes."""
    Path(output_dir).mkdir(exist_ok=True)

    # Get routes with actuals only
    routes_with_actuals = df[df['Actual'] > 0]

    winner_counts = routes_with_actuals['Winner_Model'].value_counts()

    plt.figure(figsize=(14, 8))
    ax = winner_counts.plot(kind='barh', color='steelblue')
    plt.xlabel('Number of Routes Won', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.title('Model Performance: Which Model Won Most Routes?\n(Routes with Actual Data)', fontsize=14, fontweight='bold')

    # Add count labels
    for i, v in enumerate(winner_counts.values):
        plt.text(v + 2, i, str(v), va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_winner_distribution.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/01_winner_distribution.png")
    plt.close()

def plot_average_errors(df, output_dir='visualizations'):
    """Plot average error by model."""
    Path(output_dir).mkdir(exist_ok=True)

    routes_with_actuals = df[df['Actual'] > 0]

    error_cols = [col for col in df.columns if col.endswith('_Error%') and col != 'Winner_Error%']
    avg_errors = {}

    for col in error_cols:
        model_name = col.replace('_Error%', '')
        avg_error = routes_with_actuals[col].abs().mean()
        avg_errors[model_name] = avg_error

    avg_errors_df = pd.DataFrame(list(avg_errors.items()), columns=['Model', 'Avg_MAPE'])
    avg_errors_df = avg_errors_df.sort_values('Avg_MAPE')

    plt.figure(figsize=(14, 8))
    ax = avg_errors_df.plot(x='Model', y='Avg_MAPE', kind='barh', color='coral', legend=False)
    plt.xlabel('Average MAPE (%)', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.title('Model Accuracy: Average MAPE Across All Routes\n(Lower is Better)', fontsize=14, fontweight='bold')

    # Add value labels
    for i, v in enumerate(avg_errors_df['Avg_MAPE'].values):
        plt.text(v + 5, i, f'{v:.1f}%', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_average_mape.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/02_average_mape.png")
    plt.close()

def plot_volume_accuracy(df, output_dir='visualizations'):
    """Plot total volume forecast vs actual by model."""
    Path(output_dir).mkdir(exist_ok=True)

    model_cols = [col for col in df.columns if not col.endswith('_Error%') and
                  col not in ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual', 'Winner_Model', 'Winner_Error%']]

    volume_data = []
    actual_total = df['Actual'].sum()

    for col in model_cols:
        forecast_total = df[col].sum()
        volume_error = ((forecast_total - actual_total) / actual_total * 100) if actual_total > 0 else 0
        volume_data.append({
            'Model': col,
            'Forecast': forecast_total,
            'Error%': volume_error
        })

    volume_df = pd.DataFrame(volume_data).sort_values('Error%', key=abs)

    plt.figure(figsize=(14, 8))
    colors = ['green' if abs(e) < 10 else 'orange' if abs(e) < 30 else 'red' for e in volume_df['Error%']]
    ax = volume_df.plot(x='Model', y='Error%', kind='barh', color=colors, legend=False)
    plt.xlabel('Volume Error (%)', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.title(f'Total Volume Accuracy\nActual Total: {actual_total:,.0f} pieces', fontsize=14, fontweight='bold')
    plt.axvline(x=0, color='black', linestyle='--', linewidth=1)

    # Add value labels
    for i, v in enumerate(volume_df['Error%'].values):
        plt.text(v + 2, i, f'{v:+.1f}%', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_volume_accuracy.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/03_volume_accuracy.png")
    plt.close()

def plot_error_distribution(df, output_dir='visualizations'):
    """Plot error distribution for top models."""
    Path(output_dir).mkdir(exist_ok=True)

    routes_with_actuals = df[df['Actual'] > 0]

    # Get top 6 models by winner count
    top_models = routes_with_actuals['Winner_Model'].value_counts().head(6).index

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    for idx, model in enumerate(top_models):
        error_col = f"{model}_Error%"
        if error_col in routes_with_actuals.columns:
            errors = routes_with_actuals[error_col].abs()
            errors_capped = errors.clip(upper=200)  # Cap at 200% for visualization

            axes[idx].hist(errors_capped, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
            axes[idx].set_title(f'{model}', fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('Absolute Error (%)', fontsize=10)
            axes[idx].set_ylabel('Number of Routes', fontsize=10)
            axes[idx].axvline(errors.median(), color='red', linestyle='--', linewidth=2, label=f'Median: {errors.median():.1f}%')
            axes[idx].legend()

    plt.suptitle('Error Distribution for Top 6 Models', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_error_distributions.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/04_error_distributions.png")
    plt.close()

def plot_model_heatmap(df, output_dir='visualizations'):
    """Create heatmap of model performance by route characteristics."""
    Path(output_dir).mkdir(exist_ok=True)

    routes_with_actuals = df[df['Actual'] > 0].copy()

    # Categorize routes by volume
    routes_with_actuals['Volume_Category'] = pd.cut(
        routes_with_actuals['Actual'],
        bins=[0, 10, 30, 100, np.inf],
        labels=['Very Low (0-10)', 'Low (10-30)', 'Medium (30-100)', 'High (100+)']
    )

    # Get winner distribution by volume category
    heatmap_data = routes_with_actuals.groupby(['Volume_Category', 'Winner_Model']).size().unstack(fill_value=0)

    # Get top 10 models
    top_10_models = routes_with_actuals['Winner_Model'].value_counts().head(10).index
    heatmap_data = heatmap_data[top_10_models]

    plt.figure(figsize=(14, 6))
    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', cbar_kws={'label': 'Route Count'})
    plt.title('Model Performance by Route Volume Category\n(Which Model Wins for Different Volume Levels)', fontsize=14, fontweight='bold')
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Volume Category', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_heatmap_volume_category.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/05_heatmap_volume_category.png")
    plt.close()

def plot_model_comparison_radar(df, output_dir='visualizations'):
    """Create radar chart comparing top models across multiple metrics."""
    from math import pi

    Path(output_dir).mkdir(exist_ok=True)

    routes_with_actuals = df[df['Actual'] > 0]
    top_5_models = routes_with_actuals['Winner_Model'].value_counts().head(5).index

    metrics_data = []

    for model in top_5_models:
        error_col = f"{model}_Error%"

        # Calculate metrics
        wins = len(routes_with_actuals[routes_with_actuals['Winner_Model'] == model])
        avg_error = routes_with_actuals[error_col].abs().mean()
        median_error = routes_with_actuals[error_col].abs().median()
        low_error_pct = len(routes_with_actuals[routes_with_actuals[error_col].abs() < 20]) / len(routes_with_actuals) * 100

        # Normalize to 0-100 scale (invert errors so higher is better)
        metrics_data.append({
            'Model': model,
            'Win Rate': wins / len(routes_with_actuals) * 100,
            'Accuracy (100-AvgError)': max(0, 100 - avg_error),
            'Consistency (100-MedianError)': max(0, 100 - median_error),
            'Low Error %': low_error_pct
        })

    metrics_df = pd.DataFrame(metrics_data)

    categories = ['Win Rate', 'Accuracy (100-AvgError)', 'Consistency (100-MedianError)', 'Low Error %']
    N = len(categories)

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    for idx, row in metrics_df.iterrows():
        values = row[categories].values.tolist()
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=row['Model'])
        ax.fill(angles, values, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100)
    ax.set_title('Model Performance Comparison\n(Higher is Better)', size=16, fontweight='bold', y=1.1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_radar_comparison.png', dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {output_dir}/06_radar_comparison.png")
    plt.close()

def create_summary_report(df, output_dir='visualizations'):
    """Create a text summary report."""
    Path(output_dir).mkdir(exist_ok=True)

    routes_with_actuals = df[df['Actual'] > 0]
    total_routes = len(routes_with_actuals)
    total_actual = df['Actual'].sum()

    report = []
    report.append("=" * 80)
    report.append("MODEL PERFORMANCE SUMMARY REPORT")
    report.append("=" * 80)
    report.append(f"\nTotal Routes Analyzed: {total_routes:,}")
    report.append(f"Total Actual Volume: {total_actual:,.0f} pieces")

    # Winner summary
    report.append("\n" + "-" * 80)
    report.append("TOP 10 MODELS BY ROUTES WON:")
    report.append("-" * 80)
    winner_counts = routes_with_actuals['Winner_Model'].value_counts().head(10)
    for model, count in winner_counts.items():
        pct = count / total_routes * 100
        report.append(f"{model:<40} {count:>6} routes ({pct:>5.1f}%)")

    # Average error summary
    report.append("\n" + "-" * 80)
    report.append("TOP 10 MODELS BY AVERAGE MAPE (Lower is Better):")
    report.append("-" * 80)
    error_cols = [col for col in df.columns if col.endswith('_Error%') and col != 'Winner_Error%']
    avg_errors = {}
    for col in error_cols:
        model_name = col.replace('_Error%', '')
        avg_error = routes_with_actuals[col].abs().mean()
        avg_errors[model_name] = avg_error

    for model, error in sorted(avg_errors.items(), key=lambda x: x[1])[:10]:
        report.append(f"{model:<40} {error:>6.1f}% MAPE")

    # Volume accuracy
    report.append("\n" + "-" * 80)
    report.append("TOP 10 MODELS BY VOLUME ACCURACY (Closest to 0% Error):")
    report.append("-" * 80)
    model_cols = [col for col in df.columns if not col.endswith('_Error%') and
                  col not in ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual', 'Winner_Model', 'Winner_Error%']]

    volume_errors = {}
    for col in model_cols:
        forecast_total = df[col].sum()
        volume_error = ((forecast_total - total_actual) / total_actual * 100) if total_actual > 0 else 999
        volume_errors[col] = volume_error

    for model, error in sorted(volume_errors.items(), key=lambda x: abs(x[1]))[:10]:
        report.append(f"{model:<40} {error:>+7.1f}% volume error")

    # Save report
    report_path = f'{output_dir}/00_summary_report.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report))

    print(f"📄 Saved summary report: {report_path}")
    print('\n'.join(report))

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Visualize Model Performance")
    parser.add_argument('--input', type=str, required=True, help='Path to comparison CSV')
    parser.add_argument('--output-dir', type=str, default='visualizations', help='Output directory')
    args = parser.parse_args()

    print("=" * 80)
    print("MODEL PERFORMANCE VISUALIZATION")
    print("=" * 80)

    df = load_comparison_data(args.input)

    print("\n📊 Creating visualizations...")
    create_summary_report(df, args.output_dir)
    plot_winner_distribution(df, args.output_dir)
    plot_average_errors(df, args.output_dir)
    plot_volume_accuracy(df, args.output_dir)
    plot_error_distribution(df, args.output_dir)
    plot_model_heatmap(df, args.output_dir)
    plot_model_comparison_radar(df, args.output_dir)

    print(f"\n✅ All visualizations saved to: {args.output_dir}/")
    print("\nGenerated files:")
    print("  00_summary_report.txt - Text summary")
    print("  01_winner_distribution.png - Which model won most routes")
    print("  02_average_mape.png - Average error by model")
    print("  03_volume_accuracy.png - Total volume accuracy")
    print("  04_error_distributions.png - Error distribution for top models")
    print("  05_heatmap_volume_category.png - Performance by volume category")
    print("  06_radar_comparison.png - Multi-metric comparison")

if __name__ == "__main__":
    main()
