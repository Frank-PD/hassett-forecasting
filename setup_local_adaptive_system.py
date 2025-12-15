#!/usr/bin/env python3
"""
SETUP LOCAL ADAPTIVE SYSTEM
Initialize complete adaptive forecasting system locally including:
- Performance tracking database (SQLite)
- Meta-learning model
- Routing table
- Weekly performance tracking
- Monthly routing updates

This simulates the full production system locally for testing.
"""

import pandas as pd
import sqlite3
from pathlib import Path
import sys

def setup_performance_database(db_path='local_performance_tracking.db'):
    """Create local SQLite database for performance tracking."""

    print("=" * 80)
    print("STEP 1: SETUP PERFORMANCE TRACKING DATABASE")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS performance_history")
    cursor.execute("DROP TABLE IF EXISTS routing_updates")
    cursor.execute("DROP TABLE IF EXISTS weekly_summary")

    # Create performance_history table
    cursor.execute("""
        CREATE TABLE performance_history (
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

    # Create routing_updates table
    cursor.execute("""
        CREATE TABLE routing_updates (
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

    # Create weekly_summary table
    cursor.execute("""
        CREATE TABLE weekly_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            total_routes INTEGER,
            routes_with_actuals INTEGER,
            average_mape REAL,
            median_mape REAL,
            routes_under_20pct INTEGER,
            routes_under_50pct INTEGER,
            best_model TEXT,
            worst_model TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(week_number, year)
        )
    """)

    conn.commit()
    conn.close()

    print(f"✅ Performance tracking database created: {db_path}")
    print(f"   Tables created:")
    print(f"   - performance_history: Stores weekly forecast vs actual results")
    print(f"   - routing_updates: Tracks when routes switch models")
    print(f"   - weekly_summary: Aggregated weekly performance metrics")

def setup_meta_model_directory():
    """Create directory for meta-learning models."""

    print("\n" + "=" * 80)
    print("STEP 2: SETUP META-LEARNING MODEL DIRECTORY")
    print("=" * 80)

    Path('models').mkdir(exist_ok=True)
    Path('models/meta_models').mkdir(exist_ok=True)
    Path('models/trained_models').mkdir(exist_ok=True)

    print(f"✅ Model directories created:")
    print(f"   - models/meta_models/ : Meta-learning models")
    print(f"   - models/trained_models/ : Forecasting models (SARIMA, ML, etc.)")

def setup_data_directories():
    """Create directories for data storage."""

    print("\n" + "=" * 80)
    print("STEP 3: SETUP DATA DIRECTORIES")
    print("=" * 80)

    Path('data/historical').mkdir(parents=True, exist_ok=True)
    Path('data/forecasts').mkdir(parents=True, exist_ok=True)
    Path('data/actuals').mkdir(parents=True, exist_ok=True)
    Path('data/routing_tables').mkdir(parents=True, exist_ok=True)

    print(f"✅ Data directories created:")
    print(f"   - data/historical/ : Historical shipment data")
    print(f"   - data/forecasts/ : Generated forecasts by week")
    print(f"   - data/actuals/ : Actual shipments for comparison")
    print(f"   - data/routing_tables/ : Routing table versions")

def initialize_routing_table(source_routing_table='route_model_routing_table.csv'):
    """Copy routing table to versioned storage."""

    print("\n" + "=" * 80)
    print("STEP 4: INITIALIZE ROUTING TABLE")
    print("=" * 80)

    if not Path(source_routing_table).exists():
        print(f"⚠️  Source routing table not found: {source_routing_table}")
        print(f"   Run the comprehensive comparison first to generate it.")
        return

    # Copy to versioned storage
    import shutil
    from datetime import datetime

    version = datetime.now().strftime('%Y%m%d')
    dest_path = f'data/routing_tables/routing_table_v{version}.csv'

    shutil.copy(source_routing_table, dest_path)
    shutil.copy(source_routing_table, 'data/routing_tables/routing_table_current.csv')

    routing_df = pd.read_csv(source_routing_table)

    print(f"✅ Routing table initialized:")
    print(f"   - Current version: data/routing_tables/routing_table_current.csv")
    print(f"   - Versioned backup: {dest_path}")
    print(f"   - Total routes: {len(routing_df):,}")

def create_config_file():
    """Create configuration file for the adaptive system."""

    print("\n" + "=" * 80)
    print("STEP 5: CREATE CONFIGURATION FILE")
    print("=" * 80)

    config = {
        'database': 'local_performance_tracking.db',
        'routing_table': 'data/routing_tables/routing_table_current.csv',
        'historical_data': 'data/historical/',
        'forecast_output': 'data/forecasts/',
        'actuals_input': 'data/actuals/',
        'meta_model_path': 'models/meta_models/meta_model.pkl',
        'performance_lookback_weeks': 8,
        'routing_update_threshold': 5.0,
        'min_weeks_for_update': 4,
        'retraining_frequency': 'quarterly'
    }

    import json
    with open('local_adaptive_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuration file created: local_adaptive_config.json")
    print(f"   Settings:")
    for key, value in config.items():
        print(f"   - {key}: {value}")

def create_readme():
    """Create README for the local adaptive system."""

    print("\n" + "=" * 80)
    print("STEP 6: CREATE README")
    print("=" * 80)

    readme_content = """# LOCAL ADAPTIVE FORECASTING SYSTEM

## Directory Structure

```
hassett-forecasting/
├── data/
│   ├── historical/           # Historical shipment data
│   ├── forecasts/           # Generated forecasts by week
│   ├── actuals/             # Actual shipments for validation
│   └── routing_tables/      # Routing table versions
├── models/
│   ├── meta_models/         # Meta-learning models
│   └── trained_models/      # Forecasting models (SARIMA, ML)
├── local_performance_tracking.db  # SQLite database
├── local_adaptive_config.json     # Configuration
└── src/                     # Python scripts

```

## Database Tables

### performance_history
Stores forecast vs actual results for each route/week/model
- Used to track model performance over time
- Enables monthly routing table updates

### routing_updates
Tracks when routes switch from one model to another
- Documents why changes were made
- Shows performance improvement from switch

### weekly_summary
Aggregated metrics for each week
- Overall system performance
- Best/worst performing models
- Trends over time

## Workflow

### Week 1: Initial Setup
1. Initialize database
2. Load routing table
3. Generate forecasts for Week 1
4. Save forecasts to data/forecasts/week_01.csv

### Week 2: First Performance Tracking
1. Load actual data from data/actuals/week_01.csv
2. Compare to forecasts from data/forecasts/week_01.csv
3. Calculate errors, store in performance_history
4. Generate forecasts for Week 2

### Weeks 3-4: Continue Tracking
1. Repeat Week 2 process
2. Build up performance history

### Week 5 (Monthly): Routing Update
1. Analyze last 4 weeks of performance
2. Identify routes where different model performs better
3. Update routing table
4. Continue forecasting with updated table

### Week 13 (Quarterly): Full Retraining
1. Rerun comprehensive comparison on last 12 weeks
2. Retrain meta-learning model
3. Regenerate routing table
4. Deploy updated artifacts

## Commands

### Generate Week's Forecasts
```bash
python3 run_local_forecast.py \\
  --routing-table data/routing_tables/routing_table_current.csv \\
  --historical-data "data/historical/all_data.csv" \\
  --routes-to-forecast routes_to_forecast.csv \\
  --output data/forecasts/week_XX.csv \\
  --week XX --year 2025
```

### Record Week's Performance
```bash
python3 src/performance_tracker.py \\
  --action record \\
  --week-results comparison_week_XX.csv \\
  --db local_performance_tracking.db
```

### Update Routing Table (Monthly)
```bash
python3 src/performance_tracker.py \\
  --action update \\
  --routing-table data/routing_tables/routing_table_current.csv \\
  --output data/routing_tables/routing_table_current.csv \\
  --lookback-weeks 8 \\
  --db local_performance_tracking.db
```

### View Performance Summary
```bash
python3 src/performance_tracker.py \\
  --action summary \\
  --lookback-weeks 8 \\
  --db local_performance_tracking.db
```

## Testing

See LOCAL_TESTING_GUIDE.md for detailed testing instructions.
"""

    with open('LOCAL_ADAPTIVE_README.md', 'w') as f:
        f.write(readme_content)

    print(f"✅ README created: LOCAL_ADAPTIVE_README.md")

def main():
    print("=" * 80)
    print("SETUP LOCAL ADAPTIVE FORECASTING SYSTEM")
    print("=" * 80)
    print("\nThis will create a complete adaptive forecasting system locally")
    print("including database, directories, and configuration files.\n")

    # Step 1: Database
    setup_performance_database()

    # Step 2: Model directories
    setup_meta_model_directory()

    # Step 3: Data directories
    setup_data_directories()

    # Step 4: Routing table
    initialize_routing_table()

    # Step 5: Config file
    create_config_file()

    # Step 6: README
    create_readme()

    print("\n" + "=" * 80)
    print("✅ LOCAL ADAPTIVE SYSTEM SETUP COMPLETE")
    print("=" * 80)

    print("\n📁 Files Created:")
    print("   - local_performance_tracking.db (SQLite database)")
    print("   - local_adaptive_config.json (configuration)")
    print("   - LOCAL_ADAPTIVE_README.md (documentation)")
    print("   - data/ directory structure")
    print("   - models/ directory structure")

    print("\n💡 Next Steps:")
    print("   1. Review LOCAL_ADAPTIVE_README.md")
    print("   2. Run local forecasts to test the system")
    print("   3. Simulate weekly performance tracking")
    print("   4. Test monthly routing updates")
    print("   5. Deploy to Azure Data Factory when validated")

    print("\n📚 Documentation:")
    print("   - LOCAL_ADAPTIVE_README.md - System overview")
    print("   - LOCAL_TESTING_GUIDE.md - Testing instructions")
    print("   - docs/OPERATIONAL_WORKFLOW.md - Production deployment")

if __name__ == "__main__":
    main()
