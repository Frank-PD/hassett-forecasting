#!/usr/bin/env python3
"""
PERFORMANCE TRACKING SYSTEM
Track forecast accuracy week-by-week and update model routing dynamically.

This system:
1. Stores actual vs forecast errors for each model, route, and week
2. Calculates rolling window performance (last 4-8 weeks)
3. Updates routing table based on recent performance
4. Provides continuous learning and adaptation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sqlite3

class PerformanceTracker:
    """Track and store forecast performance over time."""

    def __init__(self, db_path='performance_tracking.db'):
        """Initialize performance tracker with SQLite database."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""

        cursor = self.conn.cursor()

        # Performance history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_key TEXT NOT NULL,
                ODC TEXT,
                DDC TEXT,
                ProductType TEXT,
                dayofweek INTEGER,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                forecast_value REAL,
                actual_value REAL,
                error_pct REAL,
                absolute_error_pct REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(route_key, week_number, year, model_name)
            )
        """)

        # Model routing updates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routing_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_key TEXT NOT NULL,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                old_model TEXT,
                new_model TEXT,
                reason TEXT,
                performance_improvement REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        print(f"✅ Database initialized: {self.db_path}")

    def record_week_performance(self, week_results_df):
        """
        Record performance for all models for a specific week.

        Expected columns in week_results_df:
        - route_key, ODC, DDC, ProductType, dayofweek
        - week_number, year
        - actual_value
        - For each model: model_name_forecast, model_name_error_pct
        """

        print(f"\n📝 Recording performance for week {week_results_df['week_number'].iloc[0]}, {week_results_df['year'].iloc[0]}...")

        cursor = self.conn.cursor()
        records_added = 0

        for idx, row in week_results_df.iterrows():
            route_key = row['route_key']
            week_number = row['week_number']
            year = row['year']
            actual_value = row['actual_value']

            # Get all model columns (exclude metadata and error columns)
            exclude_cols = ['route_key', 'ODC', 'DDC', 'ProductType', 'dayofweek', 'week_number', 'year',
                           'actual_value', 'Actual', 'Winner_Model', 'Winner_Error%', 'best_model',
                           'best_error', 'confidence']
            model_cols = [col for col in week_results_df.columns
                         if not col.endswith('_Error%')
                         and not col.endswith('_error_pct')
                         and col not in exclude_cols]

            for model_col in model_cols:
                forecast_value = row[model_col]
                # Check both naming conventions for error column
                error_col = f"{model_col}_Error%"
                error_col_alt = f"{model_col}_error_pct"

                if error_col in week_results_df.columns:
                    error_pct = row[error_col]
                elif error_col_alt in week_results_df.columns:
                    error_pct = row[error_col_alt]
                else:
                    # Calculate error if not provided
                    if actual_value > 0:
                        error_pct = ((forecast_value - actual_value) / actual_value) * 100
                    else:
                        error_pct = 0 if forecast_value == 0 else 999

                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO performance_history
                        (route_key, ODC, DDC, ProductType, dayofweek, week_number, year,
                         model_name, forecast_value, actual_value, error_pct, absolute_error_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route_key, row['ODC'], row['DDC'], row['ProductType'], row['dayofweek'],
                        week_number, year, model_col, forecast_value, actual_value,
                        error_pct, abs(error_pct)
                    ))
                    records_added += 1
                except Exception as e:
                    print(f"   ⚠️  Error recording {route_key} / {model_col}: {e}")

        self.conn.commit()
        print(f"✅ Recorded {records_added:,} forecast records")

    def get_rolling_performance(self, route_key, lookback_weeks=8):
        """Get rolling window performance for a route."""

        query = """
            SELECT model_name, AVG(absolute_error_pct) as avg_error, COUNT(*) as weeks
            FROM performance_history
            WHERE route_key = ?
            AND week_number >= (SELECT MAX(week_number) FROM performance_history WHERE route_key = ?) - ?
            GROUP BY model_name
            ORDER BY avg_error ASC
        """

        df = pd.read_sql_query(query, self.conn, params=(route_key, route_key, lookback_weeks))
        return df

    def update_routing_table(self, current_routing_df, lookback_weeks=4, min_weeks=2):
        """
        Update routing table based on recent performance.

        Args:
            current_routing_df: Current routing table
            lookback_weeks: How many recent weeks to consider
            min_weeks: Minimum weeks of data required to make a change

        Returns:
            Updated routing table with new model assignments
        """

        print(f"\n🔄 Updating routing table based on last {lookback_weeks} weeks of performance...")

        updated_routing = current_routing_df.copy()
        changes = []

        for idx, row in current_routing_df.iterrows():
            route_key = row['route_key']
            current_model = row['Optimal_Model']

            # Get recent performance
            recent_perf = self.get_rolling_performance(route_key, lookback_weeks)

            if len(recent_perf) == 0 or recent_perf['weeks'].max() < min_weeks:
                # Not enough data, keep current model
                continue

            # Get best performing model
            best_model = recent_perf.iloc[0]['model_name']
            best_error = recent_perf.iloc[0]['avg_error']

            # Get current model performance
            current_perf = recent_perf[recent_perf['model_name'] == current_model]

            if len(current_perf) > 0:
                current_error = current_perf.iloc[0]['avg_error']
                improvement = current_error - best_error

                # Only switch if improvement is significant (>5% error reduction)
                if best_model != current_model and improvement > 5:
                    updated_routing.at[idx, 'Optimal_Model'] = best_model
                    updated_routing.at[idx, 'Historical_Error_Pct'] = best_error

                    changes.append({
                        'route_key': route_key,
                        'old_model': current_model,
                        'new_model': best_model,
                        'improvement': improvement,
                        'reason': f'Recent performance better by {improvement:.1f}%'
                    })

        print(f"✅ Updated {len(changes)} routes")

        if len(changes) > 0:
            changes_df = pd.DataFrame(changes)
            print(f"\n📊 Top 10 model changes:")
            print(changes_df.sort_values('improvement', ascending=False).head(10).to_string(index=False))

            # Record changes in database
            self._record_routing_updates(changes_df)

        return updated_routing

    def _record_routing_updates(self, changes_df):
        """Record routing table updates in database."""

        cursor = self.conn.cursor()

        for idx, row in changes_df.iterrows():
            cursor.execute("""
                INSERT INTO routing_updates
                (route_key, week_number, year, old_model, new_model, reason, performance_improvement)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row['route_key'],
                0,  # Will be updated with actual week
                datetime.now().year,
                row['old_model'],
                row['new_model'],
                row['reason'],
                row['improvement']
            ))

        self.conn.commit()

    def get_model_performance_summary(self, lookback_weeks=8):
        """Get overall performance summary by model."""

        query = f"""
            SELECT
                model_name,
                COUNT(DISTINCT route_key) as routes,
                AVG(absolute_error_pct) as avg_error,
                MEDIAN(absolute_error_pct) as median_error,
                MIN(absolute_error_pct) as min_error,
                MAX(absolute_error_pct) as max_error
            FROM performance_history
            WHERE week_number >= (SELECT MAX(week_number) FROM performance_history) - {lookback_weeks}
            GROUP BY model_name
            ORDER BY avg_error ASC
        """

        df = pd.read_sql_query(query, self.conn)
        return df

    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Performance Tracking System")
    parser.add_argument('--action', type=str, choices=['record', 'update', 'summary'], required=True,
                       help='Action to perform: record week results, update routing, or show summary')
    parser.add_argument('--week-results', type=str, help='Path to week results CSV (for record action)')
    parser.add_argument('--routing-table', type=str, help='Path to current routing table CSV (for update action)')
    parser.add_argument('--output', type=str, help='Output path for updated routing table')
    parser.add_argument('--lookback-weeks', type=int, default=8, help='Lookback window in weeks')
    parser.add_argument('--db', type=str, default='performance_tracking.db', help='Database path')
    args = parser.parse_args()

    print("=" * 80)
    print("PERFORMANCE TRACKING SYSTEM")
    print("=" * 80)

    tracker = PerformanceTracker(args.db)

    if args.action == 'record':
        if not args.week_results:
            print("❌ Error: --week-results required for record action")
            return

        week_results = pd.read_csv(args.week_results)
        tracker.record_week_performance(week_results)

    elif args.action == 'update':
        if not args.routing_table or not args.output:
            print("❌ Error: --routing-table and --output required for update action")
            return

        current_routing = pd.read_csv(args.routing_table)
        updated_routing = tracker.update_routing_table(current_routing, args.lookback_weeks)

        updated_routing.to_csv(args.output, index=False)
        print(f"\n✅ Updated routing table saved: {args.output}")

    elif args.action == 'summary':
        summary = tracker.get_model_performance_summary(args.lookback_weeks)
        print(f"\n📊 Model Performance Summary (Last {args.lookback_weeks} weeks):")
        print(summary.to_string(index=False))

    tracker.close()

    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
