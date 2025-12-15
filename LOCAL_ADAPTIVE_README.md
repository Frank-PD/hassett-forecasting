# LOCAL ADAPTIVE FORECASTING SYSTEM

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
python3 run_local_forecast.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data "data/historical/all_data.csv" \
  --routes-to-forecast routes_to_forecast.csv \
  --output data/forecasts/week_XX.csv \
  --week XX --year 2025
```

### Record Week's Performance
```bash
python3 src/performance_tracker.py \
  --action record \
  --week-results comparison_week_XX.csv \
  --db local_performance_tracking.db
```

### Update Routing Table (Monthly)
```bash
python3 src/performance_tracker.py \
  --action update \
  --routing-table data/routing_tables/routing_table_current.csv \
  --output data/routing_tables/routing_table_current.csv \
  --lookback-weeks 8 \
  --db local_performance_tracking.db
```

### View Performance Summary
```bash
python3 src/performance_tracker.py \
  --action summary \
  --lookback-weeks 8 \
  --db local_performance_tracking.db
```

## Testing

See LOCAL_TESTING_GUIDE.md for detailed testing instructions.
