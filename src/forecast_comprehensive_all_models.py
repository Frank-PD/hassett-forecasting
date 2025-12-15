#!/usr/bin/env python3
"""
COMPREHENSIVE ALL-MODELS COMPARISON
Includes EVERYTHING: Traditional, SARIMA, ML, Clustering, Lane-Adaptive

This will take 30-60 minutes to run but will give complete comparison.
"""

import argparse
import sys
import pickle
import warnings
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from databricks import sql
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

# Try to import SARIMA
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    SARIMA_AVAILABLE = True
except ImportError:
    SARIMA_AVAILABLE = False
    print("⚠️  SARIMA not available, will skip")

DATABRICKS_CONFIG = {
    "server_hostname": "adb-434028626745069.9.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/23a9897d305fb7e2",
    "auth_type": "databricks-oauth"
}

def connect_to_databricks():
    try:
        conn = sql.connect(**DATABRICKS_CONFIG)
        print("✅ Connected to Azure Databricks")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def load_historical_data(conn, target_week, target_year, table_name, years=4):
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

    print(f"📊 Loading {years} years of data...")
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    print(f"✅ Loaded {len(df):,} shipments")
    return df

class ComprehensiveModels:
    """All forecasting models including SARIMA, ML, Clustering."""

    # ========== TRADITIONAL MODELS (13) ==========

    @staticmethod
    def model_01_historical_baseline(route_data, target_week, target_year, product, **kwargs):
        baseline_year = 2022 if product == 'MAX' else 2024
        baseline = route_data[(route_data['week'] == target_week) & (route_data['year'] == baseline_year)]
        return baseline['pieces'].mean() if len(baseline) > 0 else 0

    @staticmethod
    def model_02_recent_2w_avg(route_data, target_week, target_year, product, **kwargs):
        recent = route_data.head(2)
        return recent['pieces'].mean() if len(recent) >= 2 else 0

    @staticmethod
    def model_03_recent_4w_avg(route_data, target_week, target_year, product, **kwargs):
        recent = route_data.head(4)
        return recent['pieces'].mean() if len(recent) >= 4 else 0

    @staticmethod
    def model_04_recent_8w_avg(route_data, target_week, target_year, product, **kwargs):
        recent = route_data.head(8)
        return recent['pieces'].mean() if len(recent) >= 8 else 0

    @staticmethod
    def model_05_trend_adjusted(route_data, target_week, target_year, product, **kwargs):
        if len(route_data) < 8:
            return route_data.head(4)['pieces'].mean() if len(route_data) >= 4 else 0
        recent_4 = route_data.head(4)['pieces'].mean()
        older_4 = route_data.iloc[4:8]['pieces'].mean()
        if older_4 > 0:
            trend_factor = max(0.5, min(1.5, recent_4 / older_4))
            return recent_4 * trend_factor
        return recent_4

    @staticmethod
    def model_06_prior_week(route_data, target_week, target_year, product, **kwargs):
        prior = route_data[route_data['week'] == target_week - 1]
        return prior['pieces'].mean() if len(prior) > 0 else 0

    @staticmethod
    def model_07_same_week_last_year(route_data, target_week, target_year, product, **kwargs):
        same_week = route_data[(route_data['week'] == target_week) & (route_data['year'] == target_year - 1)]
        return same_week['pieces'].mean() if len(same_week) > 0 else 0

    @staticmethod
    def model_08_week_specific_historical(route_data, target_week, target_year, product, **kwargs):
        week_data = route_data[route_data['week'] == target_week]
        return week_data['pieces'].mean() if len(week_data) >= 2 else 0

    @staticmethod
    def model_09_exponential_smoothing(route_data, target_week, target_year, product, **kwargs):
        if len(route_data) < 4:
            return route_data['pieces'].mean() if len(route_data) > 0 else 0
        weights = np.array([0.4, 0.3, 0.2, 0.1])
        recent_4 = route_data.head(4)['pieces'].values
        return np.sum(recent_4 * weights) if len(recent_4) == 4 else recent_4.mean()

    @staticmethod
    def model_10_probabilistic(route_data, target_week, target_year, product, **kwargs):
        prior = route_data[route_data['week'] == target_week - 1]
        prior_value = prior['pieces'].mean() if len(prior) > 0 else 0
        recent_12w = route_data.head(12)
        ship_prob = min(len(recent_12w) / 12, 1.0)
        return prior_value * ship_prob

    @staticmethod
    def model_11_hybrid_week_blend(route_data, target_week, target_year, product, **kwargs):
        week_avg = ComprehensiveModels.model_08_week_specific_historical(route_data, target_week, target_year, product)
        recent_avg = ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)
        if week_avg > 0 and recent_avg > 0:
            return 0.7 * week_avg + 0.3 * recent_avg
        return week_avg if week_avg > 0 else recent_avg

    @staticmethod
    def model_12_median_recent(route_data, target_week, target_year, product, **kwargs):
        recent = route_data.head(4)
        return recent['pieces'].median() if len(recent) >= 4 else 0

    @staticmethod
    def model_13_weighted_recent_week(route_data, target_week, target_year, product, **kwargs):
        recent = ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)
        week_specific = ComprehensiveModels.model_08_week_specific_historical(route_data, target_week, target_year, product)
        if recent > 0 and week_specific > 0:
            return 0.5 * recent + 0.5 * week_specific
        return recent if recent > 0 else week_specific

    # ========== SARIMA MODEL (14) ==========

    @staticmethod
    def model_14_sarima(route_data, target_week, target_year, product, **kwargs):
        """SARIMA(1,1,1)(1,1,1,52) - Will be slow but comprehensive."""
        if not SARIMA_AVAILABLE or len(route_data) < 52:
            return 0

        try:
            # Resample to weekly, fill gaps with 0
            df_weekly = route_data.set_index('date')['pieces'].resample('W-MON').sum()

            if len(df_weekly) < 52:
                return 0

            # Fit SARIMA
            model = SARIMAX(
                df_weekly.values,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 52),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            fitted = model.fit(disp=False, maxiter=50, method='nm')  # Faster optimizer
            forecast = fitted.forecast(steps=1)[0]
            return max(0, forecast)
        except:
            return 0

    # ========== ML MODELS (15-17) ==========

    @staticmethod
    def model_15_ml_classifier_simple_volume(route_data, target_week, target_year, product, ml_classifier=None, **kwargs):
        """ML Classifier for route selection + simple volume."""
        if ml_classifier is None:
            # Fallback to recent average if no classifier
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)

        # Extract features
        features = extract_ml_features(route_data, target_week)
        feature_vector = np.array([[
            features['shipped_last_4w'],
            features['shipped_last_8w'],
            features['shipped_last_12w'],
            features['days_since_last'],
            features['avg_volume_4w'],
            features['avg_volume_8w'],
            features['volume_trend'],
            features['volume_std'],
            features['seasonality_score'],
            features['is_new_route'],
            features['dayofweek'],
            features['week']
        ]])

        try:
            ship_prob = ml_classifier.predict_proba(feature_vector)[0][1]
            if ship_prob > 0.5:
                return route_data.head(4)['pieces'].mean() if len(route_data) >= 4 else 0
            else:
                return 0
        except:
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)

    @staticmethod
    def model_16_ml_regressor(route_data, target_week, target_year, product, ml_regressor=None, **kwargs):
        """ML Regressor for volume prediction."""
        if ml_regressor is None:
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)

        features = extract_ml_features(route_data, target_week)
        feature_vector = np.array([[
            features['shipped_last_4w'],
            features['shipped_last_8w'],
            features['shipped_last_12w'],
            features['days_since_last'],
            features['avg_volume_4w'],
            features['avg_volume_8w'],
            features['volume_trend'],
            features['volume_std'],
            features['seasonality_score'],
            features['is_new_route'],
            features['dayofweek'],
            features['week']
        ]])

        try:
            forecast = ml_regressor.predict(feature_vector)[0]
            return max(0, forecast)
        except:
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)

    @staticmethod
    def model_17_lane_adaptive(route_data, target_week, target_year, product, **kwargs):
        """Lane-adaptive: select method based on route characteristics."""
        # Calculate characteristics
        total_obs = len(route_data)
        years_active = (route_data['date'].max() - route_data['date'].min()).days / 365
        avg_volume = route_data['pieces'].mean()
        std_volume = route_data['pieces'].std()
        cv = std_volume / avg_volume if avg_volume > 0 else 999

        # Decision tree
        if years_active < 1.0:
            return route_data.head(8)['pieces'].mean() if len(route_data) >= 8 else 0
        elif cv > 0.8:
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)
        elif cv < 0.3:
            return ComprehensiveModels.model_08_week_specific_historical(route_data, target_week, target_year, product)
        else:
            return ComprehensiveModels.model_11_hybrid_week_blend(route_data, target_week, target_year, product)

    # ========== CLUSTERING MODEL (18) ==========

    @staticmethod
    def model_18_clustering(route_data, target_week, target_year, product, cluster_forecasts=None, route_cluster=None, **kwargs):
        """Clustering-based forecast: use cluster average."""
        if cluster_forecasts is None or route_cluster is None:
            return ComprehensiveModels.model_03_recent_4w_avg(route_data, target_week, target_year, product)

        return cluster_forecasts.get(route_cluster, 0)

def extract_ml_features(route_data, target_week):
    """Extract ML features for a route."""
    if len(route_data) == 0:
        return {
            'shipped_last_4w': 0, 'shipped_last_8w': 0, 'shipped_last_12w': 0,
            'days_since_last': 999, 'avg_volume_4w': 0, 'avg_volume_8w': 0,
            'volume_trend': 0, 'volume_std': 0, 'seasonality_score': 0,
            'is_new_route': 1, 'dayofweek': 0, 'week': target_week
        }

    shipped_last_4w = len(route_data.head(4))
    shipped_last_8w = len(route_data.head(8))
    shipped_last_12w = len(route_data.head(12))
    days_since_last = (pd.Timestamp.now() - route_data.iloc[0]['date']).days if len(route_data) > 0 else 999
    avg_volume_4w = route_data.head(4)['pieces'].mean() if len(route_data) >= 4 else 0
    avg_volume_8w = route_data.head(8)['pieces'].mean() if len(route_data) >= 8 else 0
    volume_std = route_data['pieces'].std() if len(route_data) > 1 else 0

    mid = len(route_data) // 2
    if mid > 0 and len(route_data) >= 8:
        recent_avg = route_data.iloc[:mid]['pieces'].mean()
        older_avg = route_data.iloc[mid:]['pieces'].mean()
        volume_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
    else:
        volume_trend = 0

    seasonality_score = len(route_data[route_data['week'] == target_week])
    is_new_route = 1 if shipped_last_12w == 0 else 0
    dayofweek = route_data.iloc[0]['dayofweek'] if len(route_data) > 0 else 0

    return {
        'shipped_last_4w': shipped_last_4w,
        'shipped_last_8w': shipped_last_8w,
        'shipped_last_12w': shipped_last_12w,
        'days_since_last': days_since_last,
        'avg_volume_4w': avg_volume_4w,
        'avg_volume_8w': avg_volume_8w,
        'volume_trend': volume_trend,
        'volume_std': volume_std,
        'seasonality_score': seasonality_score,
        'is_new_route': is_new_route,
        'dayofweek': dayofweek,
        'week': target_week
    }

def prepare_clustering(df, recent_routes):
    """Prepare clustering model."""
    print("\n🔧 Preparing clustering model...")

    # Extract features for each route
    features_list = []
    route_keys = []

    for idx, row in recent_routes.iterrows():
        route_data = df[
            (df['ODC'] == row['ODC']) &
            (df['DDC'] == row['DDC']) &
            (df['ProductType'] == row['ProductType']) &
            (df['dayofweek'] == row['dayofweek'])
        ].sort_values('date', ascending=False)

        if len(route_data) == 0:
            continue

        # Simple features for clustering
        pieces = route_data.head(12)['pieces']
        avg_volume = pieces.mean() if len(pieces) > 0 else 0
        freq = len(pieces)
        volatility = (pieces.std() / avg_volume) if avg_volume > 0 else 0

        # Handle NaN values
        avg_volume = 0 if pd.isna(avg_volume) else avg_volume
        freq = 0 if pd.isna(freq) else freq
        volatility = 0 if pd.isna(volatility) else volatility

        features_list.append([avg_volume, freq, volatility])
        route_keys.append(f"{row['ODC']}|{row['DDC']}|{row['ProductType']}|{row['dayofweek']}")

    if len(features_list) == 0:
        return {}, {}

    # Cluster
    X = StandardScaler().fit_transform(features_list)
    n_clusters = min(5, len(features_list))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)

    # Map route to cluster
    route_to_cluster = dict(zip(route_keys, clusters))

    # Calculate cluster forecast (average recent volume per cluster)
    cluster_forecasts = {}
    for cluster_id in range(n_clusters):
        cluster_routes = [route_keys[i] for i in range(len(route_keys)) if clusters[i] == cluster_id]
        cluster_volumes = []
        for route_key in cluster_routes:
            odc, ddc, product, dow = route_key.split('|')
            route_data = df[
                (df['ODC'] == odc) &
                (df['DDC'] == ddc) &
                (df['ProductType'] == product) &
                (df['dayofweek'] == int(dow))
            ].head(4)
            if len(route_data) > 0:
                cluster_volumes.append(route_data['pieces'].mean())
        cluster_forecasts[cluster_id] = np.mean(cluster_volumes) if cluster_volumes else 0

    print(f"✅ Created {n_clusters} clusters")
    return route_to_cluster, cluster_forecasts

def load_ml_models():
    """Load ML models if they exist."""
    try:
        with open('models/classifier.pkl', 'rb') as f:
            classifier = pickle.load(f)
        print("✅ Loaded ML classifier")
    except:
        classifier = None
        print("⚠️  ML classifier not found")

    try:
        with open('models/regressor.pkl', 'rb') as f:
            regressor = pickle.load(f)
        print("✅ Loaded ML regressor")
    except:
        regressor = None
        print("⚠️  ML regressor not found")

    return classifier, regressor

def run_all_models_comprehensive(conn, target_week, target_year, table_name):
    """Run ALL 18 models on ALL routes."""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ALL-MODELS COMPARISON: Week {target_week}, {target_year}")
    print(f"Running 18 models (Traditional + SARIMA + ML + Clustering + Adaptive)")
    print(f"{'='*80}\n")

    df = load_historical_data(conn, target_week, target_year, table_name, years=4)

    # Get routes
    year_start = datetime(target_year, 1, 1)
    target_date = year_start + timedelta(weeks=target_week - 1)
    recent_cutoff = target_date - timedelta(weeks=12)
    recent_routes = df[df['date'] >= recent_cutoff].groupby(
        ['ODC', 'DDC', 'ProductType', 'dayofweek']
    ).size().reset_index(name='count')

    print(f"🔍 Testing {len(recent_routes)} routes across 18 models...")
    print(f"   This will take 30-60 minutes due to SARIMA...")

    # Prepare clustering
    route_to_cluster, cluster_forecasts = prepare_clustering(df, recent_routes)

    # Load ML models
    ml_classifier, ml_regressor = load_ml_models()

    # Define all models
    models_list = [
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
        ('15_ML_Classifier_Simple_Vol', ComprehensiveModels.model_15_ml_classifier_simple_volume),
        ('16_ML_Regressor', ComprehensiveModels.model_16_ml_regressor),
        ('17_Lane_Adaptive', ComprehensiveModels.model_17_lane_adaptive),
        ('18_Clustering', ComprehensiveModels.model_18_clustering),
    ]

    all_forecasts = []
    start_time = datetime.now()

    for idx, row in recent_routes.iterrows():
        odc, ddc, product, dow = row['ODC'], row['DDC'], row['ProductType'], row['dayofweek']
        route_key = f"{odc}|{ddc}|{product}|{dow}"

        route_data = df[
            (df['ODC'] == odc) &
            (df['DDC'] == ddc) &
            (df['ProductType'] == product) &
            (df['dayofweek'] == dow)
        ].sort_values('date', ascending=False).copy()

        if len(route_data) == 0:
            continue

        # Run all models
        for model_name, model_func in models_list:
            try:
                kwargs = {
                    'ml_classifier': ml_classifier,
                    'ml_regressor': ml_regressor,
                    'cluster_forecasts': cluster_forecasts,
                    'route_cluster': route_to_cluster.get(route_key)
                }
                forecast = model_func(route_data, target_week, target_year, product, **kwargs)
                forecast = max(0, forecast)
            except Exception as e:
                forecast = 0

            all_forecasts.append({
                'ODC': odc,
                'DDC': ddc,
                'ProductType': product,
                'dayofweek': dow,
                'route_key': route_key,
                'model': model_name,
                'forecast': forecast,
                'week': target_week,
                'year': target_year
            })

        # Progress
        if (idx + 1) % 50 == 0:
            elapsed = (datetime.now() - start_time).seconds
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(recent_routes) - idx - 1) / rate if rate > 0 else 0
            print(f"   [{idx + 1}/{len(recent_routes)}] routes | {elapsed}s elapsed | ~{remaining:.0f}s remaining")

    forecast_df = pd.DataFrame(all_forecasts)
    print(f"\n✅ Generated {len(forecast_df):,} forecast records ({len(recent_routes)} routes × 18 models)")

    return forecast_df

def main():
    parser = argparse.ArgumentParser(description="Comprehensive All-Models Comparison")
    parser.add_argument('--week', type=int, required=True)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--actuals', type=str, required=True)
    parser.add_argument('--table', type=str, default='decus_domesticops_prod.dbo.tmp_hassett_report')
    parser.add_argument('--output', type=str, default='comprehensive_all_models_comparison.csv')
    args = parser.parse_args()

    conn = connect_to_databricks()

    try:
        # Generate forecasts
        forecasts_df = run_all_models_comprehensive(conn, args.week, args.year, args.table)

        # Load actuals
        actuals = pd.read_csv(args.actuals)
        actuals.columns = actuals.columns.str.strip()
        actuals['ProductType'] = actuals['Product Type']
        actuals['dayofweek'] = actuals['Day Index']
        actuals['route_key'] = (actuals['ODC'] + '|' + actuals['DDC'] + '|' +
                                 actuals['ProductType'] + '|' + actuals['dayofweek'].astype(str))
        actuals_agg = actuals.groupby('route_key').agg({'PIECES': 'sum'}).reset_index()

        # Pivot to side-by-side format
        pivot = forecasts_df.pivot_table(
            index='route_key',
            columns='model',
            values='forecast',
            aggfunc='first'
        ).reset_index()

        # Add route details
        route_details = forecasts_df[['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek']].drop_duplicates()
        pivot = pivot.merge(route_details, on='route_key')

        # Add actuals
        pivot = pivot.merge(actuals_agg, on='route_key', how='left')
        pivot['Actual'] = pivot['PIECES'].fillna(0)
        pivot = pivot.drop('PIECES', axis=1)

        # Reorder columns
        id_cols = ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'Actual']
        model_cols = [col for col in pivot.columns if col not in id_cols]
        pivot = pivot[id_cols + sorted(model_cols)]

        # Calculate errors and find winner
        for col in model_cols:
            error_col = f"{col}_Error%"
            pivot[error_col] = np.where(
                pivot['Actual'] > 0,
                ((pivot[col] - pivot['Actual']) / pivot['Actual'] * 100),
                np.where(pivot[col] > 0, 999, 0)
            )

        error_cols = [col for col in pivot.columns if col.endswith('_Error%')]
        pivot['Winner_Model'] = pivot[error_cols].abs().idxmin(axis=1).str.replace('_Error%', '')
        pivot['Winner_Error%'] = pivot[error_cols].abs().min(axis=1)

        # Save
        pivot.to_csv(args.output, index=False)
        print(f"\n💾 Saved to: {args.output}")
        print(f"   Total routes: {len(pivot):,}")
        print(f"   Total models: {len(model_cols)}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
