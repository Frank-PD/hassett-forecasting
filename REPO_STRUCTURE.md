# Hassett Forecasting - Repository Structure

## Directory Organization

```
hassett-forecasting/
├── README.md                          # Main documentation
├── QUICK_START_GUIDE.md              # Getting started guide
├── VARIANCE_AND_MULTIWEEK_GUIDE.md   # Variance & multi-week forecasting
│
├── Production Scripts
│   ├── generate_production_forecast.py    # Generate final production forecast
│   ├── calculate_forecast_variance.py     # Add confidence intervals
│   ├── forecast_multi_week.py            # 6-week outlook generator
│   ├── compare_forecast_to_actual.py     # Performance comparison
│   ├── sunday_weekly_update.sh           # Weekly workflow automation
│   └── run_local_forecast.py             # Local forecast runner
│
├── Core Forecasting
│   └── src/
│       ├── forecast_comprehensive_all_models.py  # All 18 models comparison
│       ├── performance_tracker.py                # Performance tracking & routing updates
│       ├── analyze_ensemble_routing.py           # Routing table generation
│       └── visualize_model_performance.py        # Performance charts
│
├── Setup & Utilities
│   ├── setup_local_adaptive_system.py    # Initialize local system
│   ├── prepare_test_routes.py            # Route list preparation
│   └── cleanup_repo.sh                    # Repository cleanup
│
├── Data Directories
│   ├── data/
│   │   ├── forecasts/              # Weekly forecast outputs
│   │   ├── actuals/                # Actual shipment data
│   │   ├── routing_tables/         # Model assignment tables
│   │   │   ├── routing_table_current.csv
│   │   │   └── backup/
│   │   └── performance/            # Performance comparison files
│   │
│   ├── routes_week_51.csv          # Current week routes list
│   └── route_model_routing_table.csv  # Production routing table
│
├── Production Outputs (Current Week)
│   ├── comprehensive_week51.csv           # Full 18-model comparison (in progress)
│   └── production_forecast_week51.csv     # Final production forecast (pending)
│
├── Reference Data (Week 50)
│   ├── comprehensive_all_models_week50.csv    # Week 50 full comparison
│   └── production_forecast_week50_DEMO.csv    # Week 50 production example
│
├── Archive (Old Test Files)
│   └── archive/
│       ├── old_forecasts/          # Test forecast outputs (11 files)
│       ├── old_comparisons/        # Comparison files (9 files)
│       └── old_logs/               # Log files (1 file)
│
├── Notebooks
│   └── notebooks/
│       ├── 00_setup_and_test.ipynb
│       └── 01_quick_forecast.ipynb
│
├── Documentation
│   └── docs/
│       ├── EXECUTIVE_SUMMARY_100_EXPERIMENTS.txt
│       ├── META_ANALYSIS_100_EXPERIMENTS.md
│       ├── FORECASTING_PACKAGES_USED.md
│       └── (additional guides...)
│
├── Database
│   └── local_performance_tracking.db  # SQLite performance database
│
└── Environment
    ├── venv/                       # Python virtual environment
    ├── requirements.txt
    └── .gitignore
```

## Key Production Files

### Weekly Workflow
- `sunday_weekly_update.sh` - Run every Sunday for weekly forecast
- `routes_week_XX.csv` - Routes to forecast for week XX
- `comprehensive_week_XX.csv` - Full 18-model comparison output
- `production_forecast_week_XX.csv` - Final production forecast

### Routing & Models
- `route_model_routing_table.csv` - Which model to use for each route
- `data/routing_tables/routing_table_current.csv` - Active routing assignments

### Performance Tracking
- `local_performance_tracking.db` - SQLite database with:
  - performance_history: Weekly errors per route/model
  - routing_updates: Model switch history
  - weekly_summary: Aggregated metrics

## File Naming Conventions

### Forecasts
- `production_forecast_week{XX}.csv` - Final production forecast
- `comprehensive_week{XX}.csv` - Full 18-model comparison
- `routes_week_{XX}.csv` - Routes list for week XX

### Archives
- `*_week_50_*.csv` - Old timestamped test files → archived
- `*vs_actuals*.csv` - Old comparison files → archived

## Cleanup

Archived 21 old test files to keep repository clean:
- 11 forecast test files
- 9 comparison files
- 1 log file

All archived files preserved in `archive/` directories.

## Next Steps

1. Wait for Week 51 comprehensive forecast to complete
2. Production forecast will auto-generate
3. Deploy production_forecast_week51.csv
4. Next Sunday: Run weekly update for Week 52
