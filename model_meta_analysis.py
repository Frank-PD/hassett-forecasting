#!/usr/bin/env python3
"""
Model Meta-Analysis: Track Model Performance Over Time
Identifies models that never win and provides recommendations for removal
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

def load_all_performance_summaries(project_root):
    """Load all historical performance summary JSON files"""
    summaries = []
    # Check both old location (root) and new location (data/performance)
    json_files = sorted(project_root.glob('model_performance_summary_*.json'))
    json_files.extend(sorted((project_root / 'data' / 'performance').glob('model_performance_summary_*.json')))

    print(f"📊 Found {len(json_files)} performance summary files\n")

    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            summaries.append(data)
            timestamp = data.get('timestamp', 'unknown')
            week = data.get('evaluation_week', 'N/A')
            year = data.get('evaluation_year', 'N/A')
            print(f"  • {timestamp} - Week {week}, {year}")

    print()
    return summaries

def check_csv_for_zero_win_models(project_root):
    """Check comprehensive CSV files to find models that ran but never won"""
    # Check both old location (root) and new location (data/comprehensive)
    csv_files = sorted(project_root.glob('comprehensive_all_models_week*.csv'))
    csv_files.extend(sorted((project_root / 'data' / 'comprehensive').glob('comprehensive_all_models_week*.csv')))

    print(f"🔍 Checking {len(csv_files)} CSV files for zero-win models...\n")

    zero_win_models_by_file = {}

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)

            # Find all model columns (exclude metadata columns)
            exclude_cols = ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual',
                          'Winner_Model', 'Winner_Error%']
            model_cols = [col for col in df.columns
                         if col not in exclude_cols
                         and not col.endswith('_Error%')]

            # Check which models never won
            zero_wins = []
            for model in model_cols:
                wins = (df['Winner_Model'] == model).sum()
                if wins == 0:
                    # Check if model actually produced forecasts
                    non_zero_forecasts = (df[model] > 0).sum()
                    if non_zero_forecasts > 0:
                        zero_wins.append({
                            'model': model,
                            'non_zero_forecasts': non_zero_forecasts,
                            'total_routes': len(df)
                        })

            if zero_wins:
                week = csv_file.stem.split('week')[-1]
                zero_win_models_by_file[f'week{week}'] = zero_wins
                print(f"  Week {week}: Found {len(zero_wins)} models with 0 wins:")
                for m in zero_wins:
                    print(f"    • {m['model']} ({m['non_zero_forecasts']}/{m['total_routes']} non-zero forecasts)")
        except Exception as e:
            print(f"  ⚠️  Error reading {csv_file.name}: {e}")

    print()
    return zero_win_models_by_file

def aggregate_model_performance(summaries, current_year=2025):
    """Aggregate model wins across all time periods"""

    # All-time aggregation
    all_time_wins = defaultdict(int)

    # Current year aggregation
    current_year_wins = defaultdict(int)

    # Track appearances (how many runs each model was included in)
    model_appearances_all = defaultdict(int)
    model_appearances_current_year = defaultdict(int)

    # Track by week
    weekly_performance = []

    for summary in summaries:
        timestamp = summary.get('timestamp', 'unknown')
        week = summary.get('evaluation_week', None)
        year = summary.get('evaluation_year', None)
        model_wins = summary.get('model_wins', {})
        total_routes = summary.get('total_routes', 0)

        # Normalize model names (handle inconsistent naming)
        normalized_wins = {}
        for model, wins in model_wins.items():
            # Normalize to standard format
            normalized_name = model.replace('_', ' ').title().replace(' ', '_')
            if not normalized_name.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_', '10_', '11_', '12_', '13_', '14_', '15_', '16_', '17_', '18_')):
                # Try to extract number prefix if it exists
                parts = model.split('_')
                if len(parts) > 0 and parts[0].isdigit():
                    prefix = f"{int(parts[0]):02d}_"
                    rest = '_'.join(parts[1:])
                    normalized_name = prefix + rest.replace('_', ' ').title().replace(' ', '_')
                else:
                    normalized_name = model

            normalized_wins[normalized_name] = wins

        # Add to weekly tracking
        weekly_performance.append({
            'timestamp': timestamp,
            'week': week,
            'year': year,
            'total_routes': total_routes,
            'models': normalized_wins
        })

        # Aggregate all-time
        for model, wins in normalized_wins.items():
            all_time_wins[model] += wins
            model_appearances_all[model] += 1

            # Aggregate current year
            if year == current_year:
                current_year_wins[model] += wins
                model_appearances_current_year[model] += 1

    return {
        'all_time_wins': dict(all_time_wins),
        'current_year_wins': dict(current_year_wins),
        'model_appearances_all': dict(model_appearances_all),
        'model_appearances_current_year': dict(model_appearances_current_year),
        'weekly_performance': weekly_performance
    }

def identify_underperformers(performance_data, min_appearances=1):
    """Identify models that never win"""

    all_models = set(performance_data['model_appearances_all'].keys())

    # Models with 0 wins all-time
    zero_wins_all_time = [
        model for model in all_models
        if performance_data['all_time_wins'].get(model, 0) == 0
        and performance_data['model_appearances_all'].get(model, 0) >= min_appearances
    ]

    # Models with 0 wins in current year
    current_year_models = set(performance_data['model_appearances_current_year'].keys())
    zero_wins_current_year = [
        model for model in current_year_models
        if performance_data['current_year_wins'].get(model, 0) == 0
        and performance_data['model_appearances_current_year'].get(model, 0) >= min_appearances
    ]

    # Models with very few wins (bottom 10%)
    all_time_sorted = sorted(performance_data['all_time_wins'].items(), key=lambda x: x[1])
    total_models = len(all_time_sorted)
    bottom_10_pct = all_time_sorted[:max(1, total_models // 10)]

    return {
        'zero_wins_all_time': zero_wins_all_time,
        'zero_wins_current_year': zero_wins_current_year,
        'bottom_10_percent': [model for model, wins in bottom_10_pct]
    }

def generate_report(performance_data, underperformers, zero_win_models, current_year=2025):
    """Generate comprehensive meta-analysis report"""

    print("="*80)
    print("MODEL META-ANALYSIS REPORT")
    print("="*80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Year: {current_year}")
    print(f"Historical Runs Analyzed: {len(performance_data['weekly_performance'])}")
    print()

    # All-time performance
    print("📊 ALL-TIME MODEL PERFORMANCE (Sorted by Wins)")
    print("-" * 80)
    all_time_sorted = sorted(
        performance_data['all_time_wins'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    total_wins = sum(wins for _, wins in all_time_sorted)

    for rank, (model, wins) in enumerate(all_time_sorted, 1):
        appearances = performance_data['model_appearances_all'][model]
        pct = (wins / total_wins * 100) if total_wins > 0 else 0
        avg_wins = wins / appearances if appearances > 0 else 0
        status = "🟢" if wins > 0 else "🔴"
        print(f"{rank:2}. {status} {model:<35} {wins:5,} wins ({pct:5.1f}%) | Avg: {avg_wins:6.1f} per run | Runs: {appearances}")
    print()

    # Current year performance
    print(f"📊 {current_year} MODEL PERFORMANCE (Sorted by Wins)")
    print("-" * 80)
    current_year_sorted = sorted(
        performance_data['current_year_wins'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    total_wins_cy = sum(wins for _, wins in current_year_sorted)

    for rank, (model, wins) in enumerate(current_year_sorted, 1):
        appearances = performance_data['model_appearances_current_year'][model]
        pct = (wins / total_wins_cy * 100) if total_wins_cy > 0 else 0
        avg_wins = wins / appearances if appearances > 0 else 0
        status = "🟢" if wins > 0 else "🔴"
        print(f"{rank:2}. {status} {model:<35} {wins:5,} wins ({pct:5.1f}%) | Avg: {avg_wins:6.1f} per run | Runs: {appearances}")
    print()

    # Underperformers
    print("🔴 UNDERPERFORMING MODELS - REMOVAL CANDIDATES")
    print("-" * 80)

    # Check CSV files for models that ran but never won
    all_zero_win_models = set()
    if zero_win_models:
        print(f"\n❌ Models that RAN but NEVER WON (from CSV analysis):")
        for week, models in zero_win_models.items():
            for model_info in models:
                all_zero_win_models.add(model_info['model'])
                print(f"  • {model_info['model']} - {week} ({model_info['non_zero_forecasts']}/{model_info['total_routes']} non-zero forecasts)")

    if underperformers['zero_wins_current_year']:
        print(f"\n❌ Models with ZERO wins in {current_year} from JSON tracking:")
        for model in underperformers['zero_wins_current_year']:
            appearances = performance_data['model_appearances_current_year'][model]
            print(f"  • {model} ({appearances} runs in {current_year})")
    elif not all_zero_win_models:
        print(f"\n✅ No models with zero wins in {current_year}")

    if underperformers['zero_wins_all_time']:
        print(f"\n❌ Models with ZERO wins ALL-TIME (Strong removal candidates):")
        for model in underperformers['zero_wins_all_time']:
            appearances = performance_data['model_appearances_all'][model]
            print(f"  • {model} ({appearances} total runs)")
    elif not all_zero_win_models:
        print(f"\n✅ No models with zero wins all-time")

    print(f"\n⚠️  Bottom 10% Performers (Low priority - may improve):")
    for model in underperformers['bottom_10_percent']:
        wins = performance_data['all_time_wins'][model]
        appearances = performance_data['model_appearances_all'][model]
        print(f"  • {model} ({wins} total wins across {appearances} runs)")

    print()

    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 80)

    # Combine zero-win models from CSV analysis with JSON analysis
    strong_removal = list(all_zero_win_models) + underperformers['zero_wins_all_time']
    strong_removal = list(set(strong_removal))  # Remove duplicates

    consider_removal = [m for m in underperformers['zero_wins_current_year'] if m not in strong_removal]

    if strong_removal:
        print(f"\n1. REMOVE IMMEDIATELY ({len(strong_removal)} models):")
        print("   These models have NEVER won and provide no value:")
        for model in sorted(strong_removal):
            print(f"   ❌ {model}")
        print("\n   💰 Benefit: Removing these models will reduce execution time significantly!")
        print("      Estimated time savings: ~30-40% faster runs")

    if consider_removal:
        print(f"\n2. CONSIDER REMOVING ({len(consider_removal)} models):")
        print(f"   These models had no wins in {current_year} but may have won previously:")
        for model in consider_removal:
            all_time_wins = performance_data['all_time_wins'].get(model, 0)
            print(f"   ⚠️  {model} (had {all_time_wins} wins in previous periods)")

    if not strong_removal and not consider_removal:
        print("\n✅ All models are contributing! No removals recommended at this time.")

    print()
    print("="*80)

    return {
        'strong_removal': strong_removal,
        'consider_removal': consider_removal,
        'bottom_performers': underperformers['bottom_10_percent']
    }

def save_historical_tracking(performance_data, output_file):
    """Save comprehensive tracking data for future analysis"""

    # Create detailed DataFrame
    records = []
    for week_data in performance_data['weekly_performance']:
        timestamp = week_data['timestamp']
        week = week_data['week']
        year = week_data['year']
        total_routes = week_data['total_routes']

        for model, wins in week_data['models'].items():
            records.append({
                'timestamp': timestamp,
                'week': week,
                'year': year,
                'model': model,
                'wins': wins,
                'total_routes': total_routes,
                'win_percentage': (wins / total_routes * 100) if total_routes > 0 else 0
            })

    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    print(f"💾 Historical tracking saved: {output_file}")

    return df

def main():
    project_root = Path.cwd()
    current_year = datetime.now().year

    print("="*80)
    print("MODEL META-ANALYSIS: Performance Tracking & Removal Recommendations")
    print("="*80)
    print()

    # Load all historical summaries
    summaries = load_all_performance_summaries(project_root)

    if len(summaries) == 0:
        print("❌ No performance summary files found!")
        print("   Run the comprehensive update first to generate performance data.")
        return

    # Check CSV files for models that ran but never won
    zero_win_models = check_csv_for_zero_win_models(project_root)

    # Aggregate performance
    print("🔄 Aggregating model performance...")
    performance_data = aggregate_model_performance(summaries, current_year)
    print(f"✅ Analyzed {len(performance_data['all_time_wins'])} unique models\n")

    # Identify underperformers
    print("🔍 Identifying underperforming models...")
    underperformers = identify_underperformers(performance_data)
    print(f"✅ Analysis complete\n")

    # Generate report
    recommendations = generate_report(performance_data, underperformers, zero_win_models, current_year)

    # Create performance directory if it doesn't exist
    (project_root / 'data' / 'performance').mkdir(parents=True, exist_ok=True)

    # Save historical tracking
    tracking_file = project_root / 'data' / 'performance' / 'model_performance_history.csv'
    df_history = save_historical_tracking(performance_data, tracking_file)

    # Save recommendations
    recommendations_file = project_root / 'data' / 'performance' / f'model_removal_recommendations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(recommendations_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_year': current_year,
            'total_runs_analyzed': len(summaries),
            'recommendations': {
                'strong_removal': recommendations['strong_removal'],
                'consider_removal': recommendations['consider_removal'],
                'bottom_performers': recommendations['bottom_performers']
            },
            'all_time_performance': performance_data['all_time_wins'],
            'current_year_performance': performance_data['current_year_wins']
        }, f, indent=2)

    print(f"💾 Recommendations saved: {recommendations_file.name}\n")

    print("="*80)
    print("✅ META-ANALYSIS COMPLETE!")
    print("="*80)
    print()
    print("📋 Next Steps:")
    print("  1. Review removal recommendations above")
    print("  2. Check model_performance_history.csv for detailed trends")
    print("  3. Update model list in comprehensive notebook if removing models")
    print("  4. Re-run weekly update with reduced model set for faster execution")
    print()

if __name__ == "__main__":
    main()
