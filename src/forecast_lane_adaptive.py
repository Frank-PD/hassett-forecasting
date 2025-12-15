#!/usr/bin/env python3
"""
LANE-ADAPTIVE FORECASTING
Determine forecasting method PER LANE based on lane characteristics

Key Insight: Different lanes have different patterns:
  - Stable lanes → SARIMA or Exponential Smoothing
  - Volatile lanes → Recent average
  - Trending lanes → Trend-adjusted
  - Sporadic lanes → Probabilistic
  - New lanes → Clustering

This selects the BEST method for each lane based on:
  - Stability (coefficient of variation)
  - Trend direction (growing/declining/stable)
  - Frequency (daily vs sporadic)
  - Data availability (years of history)
  - Recent anomalies (is pattern breaking?)
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql

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

def classify_lane(lane_data, target_week):
    """
    Classify lane based on characteristics to determine best forecasting method.

    Returns: dict with lane characteristics and recommended method
    """
    # Calculate characteristics
    total_obs = len(lane_data)
    years_active = (lane_data['date'].max() - lane_data['date'].min()).days / 365
    avg_volume = lane_data['pieces'].mean()
    std_volume = lane_data['pieces'].std()
    cv = std_volume / avg_volume if avg_volume > 0 else 999  # Coefficient of variation

    # Frequency: days shipped per year
    days_per_year = total_obs / years_active if years_active > 0 else 0

    # Trend: compare recent half vs older half
    mid = len(lane_data) // 2
    if mid > 0:
        recent_avg = lane_data.iloc[:mid]['pieces'].mean()  # More recent
        older_avg = lane_data.iloc[mid:]['pieces'].mean()
        trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
    else:
        trend = 0

    # Week-specific history (for target week)
    week_specific = lane_data[lane_data['week'] == target_week]
    week_history_count = len(week_specific)

    # Anomaly detection: is recent data diverging from historical?
    if len(lane_data) >= 8:
        recent_4w = lane_data.head(4)['pieces'].mean()
        historical_avg = lane_data['pieces'].mean()
        anomaly_ratio = recent_4w / historical_avg if historical_avg > 0 else 1.0
        is_anomaly = anomaly_ratio < 0.5 or anomaly_ratio > 2.0
    else:
        is_anomaly = False
        anomaly_ratio = 1.0

    characteristics = {
        'total_observations': total_obs,
        'years_active': years_active,
        'avg_volume': avg_volume,
        'coefficient_of_variation': cv,
        'days_per_year': days_per_year,
        'trend': trend,
        'week_specific_history': week_history_count,
        'is_anomaly': is_anomaly,
        'anomaly_ratio': anomaly_ratio
    }

    # DECISION TREE: Select method based on characteristics

    # Rule 1: New lanes (<1 year) → Use clustering
    if years_active < 1.0:
        method = 'clustering'
        confidence = 0.35
        reason = f'New lane ({years_active:.1f} years)'

    # Rule 2: Sporadic lanes (<100 days/year) → Probabilistic
    elif days_per_year < 100:
        method = 'probabilistic'
        confidence = 0.45
        reason = f'Sporadic ({days_per_year:.0f} days/year)'

    # Rule 3: Anomaly detected → Recent average ONLY (ignore history)
    elif is_anomaly:
        method = 'recent_average_2w'
        confidence = 0.50
        reason = f'Anomaly detected (recent {anomaly_ratio:.2f}x historical)'

    # Rule 4: High volatility (CV > 0.8) → Simple recent average
    elif cv > 0.8:
        method = 'recent_average_4w'
        confidence = 0.60
        reason = f'High volatility (CV={cv:.2f})'

    # Rule 5: Strong declining trend (<-0.3) → Trend-adjusted recent
    elif trend < -0.3:
        method = 'trend_adjusted'
        confidence = 0.65
        reason = f'Declining trend ({trend:+.1%})'

    # Rule 6: Strong growing trend (>0.3) → Trend-adjusted
    elif trend > 0.3:
        method = 'trend_adjusted'
        confidence = 0.65
        reason = f'Growing trend ({trend:+.1%})'

    # Rule 7: Stable, frequent, long history → Week-specific historical
    elif cv < 0.3 and days_per_year >= 250 and week_history_count >= 3:
        method = 'week_specific_historical'
        confidence = 0.85
        reason = f'Stable, frequent, week-specific history ({week_history_count} years)'

    # Rule 8: Moderate stability with week history → Hybrid approach
    elif cv < 0.5 and week_history_count >= 2:
        method = 'hybrid_week_specific'
        confidence = 0.75
        reason = f'Moderate stability, some week history'

    # Rule 9: Default → Recent 4-week average
    else:
        method = 'recent_average_4w'
        confidence = 0.60
        reason = f'Default (CV={cv:.2f}, {days_per_year:.0f} days/yr)'

    characteristics['method'] = method
    characteristics['confidence'] = confidence
    characteristics['reason'] = reason

    return characteristics

def forecast_by_method(lane_data, method, target_week, odc, ddc, product, dow):
    """
    Apply the selected forecasting method to generate forecast.
    """
    if method == 'clustering':
        # Use cluster average (simplified: use overall average of similar frequency routes)
        forecast = lane_data.tail(8)['pieces'].mean() if len(lane_data) >= 8 else 0

    elif method == 'probabilistic':
        # Probabilistic: prior week × shipping probability
        if len(lane_data) > 0:
            prior_week = lane_data.head(1)['pieces'].values[0] if len(lane_data) >= 1 else 0
            ship_prob = min(len(lane_data) / 12, 1.0)  # Shipped N times in last 12 weeks
            forecast = prior_week * ship_prob
        else:
            forecast = 0

    elif method == 'recent_average_2w':
        # Recent 2-week average (for anomaly situations)
        forecast = lane_data.head(2)['pieces'].mean() if len(lane_data) >= 2 else 0

    elif method == 'recent_average_4w':
        # Standard 4-week average
        forecast = lane_data.head(4)['pieces'].mean() if len(lane_data) >= 4 else 0

    elif method == 'trend_adjusted':
        # Trend-adjusted: recent average × trend factor
        if len(lane_data) >= 8:
            recent_4w = lane_data.head(4)['pieces'].mean()
            older_4w = lane_data.iloc[4:8]['pieces'].mean()
            trend_factor = recent_4w / older_4w if older_4w > 0 else 1.0
            trend_factor = max(0.5, min(1.5, trend_factor))  # Cap at ±50%
            forecast = recent_4w * trend_factor
        else:
            forecast = lane_data['pieces'].mean() if len(lane_data) > 0 else 0

    elif method == 'week_specific_historical':
        # Use historical average for this specific week
        week_specific = lane_data[lane_data['week'] == target_week]
        forecast = week_specific['pieces'].mean() if len(week_specific) > 0 else lane_data['pieces'].mean()

    elif method == 'hybrid_week_specific':
        # Blend: 60% week-specific historical + 40% recent average
        week_specific = lane_data[lane_data['week'] == target_week]
        if len(week_specific) >= 2:
            week_avg = week_specific['pieces'].mean()
            recent_avg = lane_data.head(4)['pieces'].mean() if len(lane_data) >= 4 else week_avg
            forecast = 0.6 * week_avg + 0.4 * recent_avg
        else:
            forecast = lane_data.head(4)['pieces'].mean() if len(lane_data) >= 4 else 0

    else:
        # Fallback
        forecast = lane_data.head(4)['pieces'].mean() if len(lane_data) >= 4 else 0

    return max(0, forecast)  # Never negative

def load_multi_year_data(conn, target_week, target_year, table_name, years=4):
    """Load multi-year data for comprehensive analysis."""
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
    print(f"   Date range: {lookback_date.date()} to {target_date.date()}")

    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ Loaded {len(df):,} shipments")

    return df

def generate_lane_adaptive_forecast(conn, target_week, target_year, table_name):
    """
    Generate forecast using lane-adaptive method selection.
    Each lane gets the best method based on its characteristics.
    """
    print(f"\n{'='*80}")
    print(f"LANE-ADAPTIVE FORECASTING: Week {target_week}, {target_year}")
    print(f"Dynamic Method Selection Per Lane")
    print(f"{'='*80}\n")

    # Load 4 years of data
    df = load_multi_year_data(conn, target_week, target_year, table_name, years=4)

    # Get all unique route-day combinations from recent 12 weeks
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    recent_cutoff = target_date - timedelta(weeks=12)

    recent_lanes = df[df['date'] >= recent_cutoff].groupby(
        ['ODC', 'DDC', 'ProductType', 'dayofweek']
    ).size().reset_index(name='count')

    print(f"\n🔍 Analyzing {len(recent_lanes)} potential lanes...")
    print(f"   Classifying each lane and selecting best method...")

    forecasts = []
    method_counts = {}

    for idx, row in recent_lanes.iterrows():
        odc = row['ODC']
        ddc = row['DDC']
        product = row['ProductType']
        dow = row['dayofweek']

        # Get lane history
        lane_data = df[
            (df['ODC'] == odc) &
            (df['DDC'] == ddc) &
            (df['ProductType'] == product) &
            (df['dayofweek'] == dow)
        ].sort_values('date', ascending=False).copy()

        if len(lane_data) == 0:
            continue

        # Classify lane and select method
        lane_chars = classify_lane(lane_data, target_week)
        method = lane_chars['method']
        confidence = lane_chars['confidence']

        # Count methods
        method_counts[method] = method_counts.get(method, 0) + 1

        # Generate forecast using selected method
        forecast = forecast_by_method(lane_data, method, target_week, odc, ddc, product, dow)

        if forecast > 0:  # Only include if forecast > 0
            forecasts.append({
                'ODC': odc,
                'DDC': ddc,
                'ProductType': product,
                'dayofweek': dow,
                'forecast': forecast,
                'method': method,
                'confidence': confidence,
                'cv': lane_chars['coefficient_of_variation'],
                'trend': lane_chars['trend'],
                'years_active': lane_chars['years_active'],
                'week_history': lane_chars['week_specific_history'],
                'reason': lane_chars['reason'],
                'week': target_week,
                'year': target_year
            })

        # Progress
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(recent_lanes)} lanes...")

    forecast_df = pd.DataFrame(forecasts)

    # Summary
    print(f"\n✅ Lane-Adaptive Forecast Generated:")
    print(f"   Total lanes: {len(forecast_df)}")
    print(f"   Total pieces: {forecast_df['forecast'].sum():,.0f}")

    print(f"\n📊 Method Distribution:")
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(forecast_df) * 100 if len(forecast_df) > 0 else 0
        print(f"   {method:<30} {count:>6} lanes ({pct:>5.1f}%)")

    print(f"\n📦 By Product:")
    for product in ['MAX', 'EXP']:
        product_forecast = forecast_df[forecast_df['ProductType'] == product]['forecast'].sum()
        product_lanes = len(forecast_df[forecast_df['ProductType'] == product])
        print(f"   {product}: {product_forecast:,.0f} pieces ({product_lanes} lanes)")

    print(f"\n📈 Confidence Distribution:")
    high_conf = len(forecast_df[forecast_df['confidence'] >= 0.7])
    med_conf = len(forecast_df[(forecast_df['confidence'] >= 0.5) & (forecast_df['confidence'] < 0.7)])
    low_conf = len(forecast_df[forecast_df['confidence'] < 0.5])
    print(f"   High (≥70%):     {high_conf} lanes")
    print(f"   Medium (50-70%): {med_conf} lanes")
    print(f"   Low (<50%):      {low_conf} lanes")

    return forecast_df

def save_forecast(forecast, output_path=None):
    """Save forecast to CSV."""
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"lane_adaptive_week_{forecast['week'].iloc[0]}_{forecast['year'].iloc[0]}_{timestamp}.csv"

    output_path = Path(output_path)
    forecast.to_csv(output_path, index=False)
    print(f"\n💾 Forecast saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="LANE-ADAPTIVE: Dynamic Method Selection Per Lane"
    )
    parser.add_argument('--week', type=int, required=True, help='Target week (1-53)')
    parser.add_argument('--year', type=int, required=True, help='Target year')
    parser.add_argument('--output', type=str, default=None, help='Output CSV path')
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"LANE-ADAPTIVE HASSETT FORECASTING")
    print(f"Each Lane Gets the Best Method for Its Characteristics")
    print(f"{'='*80}\n")

    conn = connect_to_databricks()

    try:
        forecast = generate_lane_adaptive_forecast(conn, args.week, args.year, args.table)

        if len(forecast) > 0:
            save_forecast(forecast, args.output)
            print(f"\n{'='*80}")
            print(f"✅ LANE-ADAPTIVE FORECAST COMPLETE!")
            print(f"{'='*80}\n")
        else:
            print("❌ Forecast generation failed")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
