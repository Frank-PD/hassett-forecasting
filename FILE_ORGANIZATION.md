# File Organization Guide

## Current Issue
Outputs are currently saved to project root, creating clutter:
```
project_root/
├── comprehensive_all_models_week50.csv     ← Should be in data/
├── production_forecast_week51.csv           ← Should be in data/
├── model_performance_summary_*.json         ← Should be in data/
└── route_model_routing_*.csv                ← Should be in data/
```

## Recommended Structure

```
hassett-forecasting/
│
├── data/                              # All data outputs (git-ignored)
│   ├── forecasts/                     # Production forecasts
│   │   ├── production_forecast_week50.csv
│   │   ├── production_forecast_week51.csv
│   │   └── production_forecast_week52.csv
│   │
│   ├── comprehensive/                 # Full model comparisons
│   │   ├── comprehensive_all_models_week50.csv
│   │   ├── comprehensive_all_models_week51.csv
│   │   └── comprehensive_all_models_week52.csv
│   │
│   ├── routing_tables/                # Model routing tables
│   │   ├── route_model_routing_table.csv (current/latest)
│   │   ├── route_model_routing_20251215_125056.csv
│   │   └── route_model_routing_20251216_090000.csv
│   │
│   ├── performance/                   # Performance tracking
│   │   ├── model_performance_summary_20251215_125056.json
│   │   ├── model_performance_history.csv
│   │   └── model_removal_recommendations_20251215_132016.json
│   │
│   ├── actuals/                       # Actual shipment data (if cached)
│   │   └── actuals_week50_2025.csv
│   │
│   └── historical/                    # Historical data extracts (if cached)
│       └── historical_4years_20251215.csv
│
├── docs/                              # Documentation (git-tracked)
│   ├── FORECASTING_SYSTEM_JOURNEY.md
│   ├── ORCHESTRATION_GUIDE_BUSINESS.md
│   ├── SYSTEM_IMPROVEMENTS.md
│   ├── WEEKLY_UPDATE_GUIDE.md
│   └── FILE_ORGANIZATION.md (this file)
│
├── src/                               # Source code (git-tracked)
│   ├── forecast_comprehensive_all_models.py
│   └── ...
│
├── notebooks/                         # Jupyter notebooks (git-tracked)
│   └── 99_comprehensive_weekly_update.ipynb
│
├── scripts/                           # Utility scripts (git-tracked)
│   ├── run_comprehensive_update.py
│   └── model_meta_analysis.py
│
├── models/                            # ML model artifacts (git-ignored)
│   ├── classifier.pkl
│   └── regressor.pkl
│
├── venv/                              # Python environment (git-ignored)
│
├── .gitignore                         # Git ignore rules
├── requirements.txt                   # Python dependencies
└── README.md                          # Project overview
```

## What Goes Where?

### data/ - All Generated Data (Git-Ignored)
**Purpose:** Store all data outputs, temporary files, and generated artifacts
**Git Status:** Ignored (too large, changes frequently)
**Files:**
- Production forecasts
- Comprehensive comparisons
- Routing tables
- Performance summaries
- Cached actuals/historical data

### docs/ - Documentation (Git-Tracked)
**Purpose:** User guides, business documentation, technical specs
**Git Status:** Tracked (important for team knowledge)
**Files:**
- System journey
- Orchestration guide
- Weekly update guide
- Technical documentation

### src/ - Source Code (Git-Tracked)
**Purpose:** Core forecasting logic and model implementations
**Git Status:** Tracked (the actual code)
**Files:**
- Model implementations
- Utility functions
- Database connectors

### scripts/ - Executable Scripts (Git-Tracked)
**Purpose:** Main execution scripts and tools
**Git Status:** Tracked (how to run the system)
**Files:**
- run_comprehensive_update.py
- model_meta_analysis.py
- Other automation scripts

### notebooks/ - Jupyter Notebooks (Git-Tracked)
**Purpose:** Interactive analysis and exploration
**Git Status:** Tracked (analysis workflows)
**Files:**
- Weekly update notebook
- Experimental notebooks
- Demo notebooks

## Migration Plan

### Step 1: Create Directory Structure
```bash
mkdir -p data/forecasts
mkdir -p data/comprehensive
mkdir -p data/routing_tables
mkdir -p data/performance
mkdir -p data/actuals
mkdir -p data/historical
```

### Step 2: Move Existing Files
```bash
# Move forecasts
mv production_forecast_*.csv data/forecasts/

# Move comprehensive comparisons
mv comprehensive_all_models_*.csv data/comprehensive/

# Move routing tables
mv route_model_routing_*.csv data/routing_tables/

# Move performance files
mv model_performance_*.json data/performance/
mv model_performance_history.csv data/performance/
mv model_removal_recommendations_*.json data/performance/
```

### Step 3: Update Scripts
Update `run_comprehensive_update.py` to use new paths:
```python
# Old
output_file = project_root / f'comprehensive_all_models_week{N}.csv'

# New
output_file = project_root / 'data' / 'comprehensive' / f'comprehensive_all_models_week{N}.csv'
```

### Step 4: Update .gitignore
```
# Add to .gitignore
data/forecasts/*.csv
data/comprehensive/*.csv
data/routing_tables/*.csv
data/performance/*.json
data/performance/*.csv
data/actuals/*.csv
data/historical/*.csv
models/*.pkl
```

## Benefits of This Structure

### 1. Clean Repository
```
Before:
├── 50+ CSV files in root
├── Multiple JSON files scattered
└── Hard to find anything

After:
├── Organized by purpose
├── Easy to find specific outputs
└── Clean git status
```

### 2. Better Collaboration
- Team knows where to find files
- Clear separation of code vs data
- Easy to share specific outputs

### 3. Git Efficiency
- Data files not in version control
- Smaller repo size
- Faster clone/pull operations

### 4. Easier Cleanup
```bash
# Remove all old forecasts
rm data/forecasts/*week4*.csv

# Clear performance tracking
rm data/performance/*202412*.json

# Full cleanup
rm -rf data/*
```

## File Naming Conventions

### Production Forecasts
```
Format: production_forecast_week{N}.csv
Example: production_forecast_week51.csv

Purpose: The forecast to use for planning
Location: data/forecasts/
```

### Comprehensive Comparisons
```
Format: comprehensive_all_models_week{N}.csv
Example: comprehensive_all_models_week50.csv

Purpose: All 14 models vs actuals for analysis
Location: data/comprehensive/
```

### Routing Tables
```
Format: route_model_routing_{timestamp}.csv
Example: route_model_routing_20251215_125056.csv

Special: route_model_routing_table.csv (always latest)

Purpose: Which model won for each route
Location: data/routing_tables/
```

### Performance Summaries
```
Format: model_performance_summary_{timestamp}.json
Example: model_performance_summary_20251215_125056.json

Purpose: Model win counts for meta-analysis
Location: data/performance/
```

### Performance History
```
Format: model_performance_history.csv
Example: model_performance_history.csv

Purpose: Aggregated weekly tracking of all models
Location: data/performance/
```

### Removal Recommendations
```
Format: model_removal_recommendations_{timestamp}.json
Example: model_removal_recommendations_20251215_132016.json

Purpose: Automated recommendations from meta-analysis
Location: data/performance/
```

## Retention Policy

### Keep Forever
- Latest production forecast
- Latest routing table
- model_performance_history.csv (aggregated trends)

### Keep 12 Weeks
- Historical forecasts (for comparison)
- Comprehensive comparisons (for deep dives)
- Timestamped routing tables (for audit trail)

### Keep 4 Weeks
- Performance summaries (JSONs)
- Removal recommendations

### Cleanup Script
```bash
#!/bin/bash
# cleanup_old_data.sh

# Remove forecasts older than 12 weeks
find data/forecasts -name "*.csv" -mtime +84 -delete

# Remove comprehensive comparisons older than 12 weeks
find data/comprehensive -name "*.csv" -mtime +84 -delete

# Remove performance JSONs older than 4 weeks
find data/performance -name "*.json" -mtime +28 -delete

# Keep latest routing table, remove old timestamped ones older than 12 weeks
find data/routing_tables -name "route_model_routing_*.csv" -mtime +84 -delete

echo "Cleanup complete!"
```

## Access Patterns

### For Business Users
**What you need:** Latest production forecast
**Where to find:** `data/forecasts/production_forecast_week{current}.csv`
**How often:** Weekly (Monday morning)

### For Analysts
**What you need:** Historical trends and comparisons
**Where to find:**
- `data/comprehensive/` - Detailed model comparisons
- `data/performance/model_performance_history.csv` - Trend analysis
**How often:** As needed for analysis

### For Technical Team
**What you need:** All outputs for debugging/optimization
**Where to find:** All subfolders in `data/`
**How often:** After each run

### For Auditors
**What you need:** Timestamped snapshots showing decisions
**Where to find:**
- `data/routing_tables/route_model_routing_{timestamp}.csv`
- `data/performance/model_performance_summary_{timestamp}.json`
**How often:** As needed for compliance

## Next Steps

1. **Create directory structure** (see Step 1 above)
2. **Run updated script** with new output paths
3. **Move existing files** to proper locations (optional cleanup)
4. **Update .gitignore** to exclude data files
5. **Update team documentation** with new file locations

## Questions?

- **Where's the production forecast?** → `data/forecasts/`
- **Where are detailed comparisons?** → `data/comprehensive/`
- **Where's performance tracking?** → `data/performance/`
- **Where's the latest routing?** → `data/routing_tables/route_model_routing_table.csv`

---

**Last Updated:** December 15, 2025
**Status:** Recommended structure (implement in next update)
