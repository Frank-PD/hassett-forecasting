# Repository Cleanup Plan

## 🎯 Goal
Remove outdated, duplicate, and unnecessary files to keep the repo clean and maintainable.

---

## 📋 Files to DELETE (Safe to Remove)

### Old Data Files (Root Directory)
```bash
# These are old format or temporary data files - all superseded by data/ folder
comprehensive_week51.csv                        # Old format, now in data/comprehensive/
routes_week_51.csv                              # Old format
week_51_forecasts.csv                           # Old format
trend_week_50_2025_20251212_141141.csv         # Old analysis file
test_routes.csv                                 # Test file, not needed

# Command to remove:
rm comprehensive_week51.csv routes_week_51.csv week_51_forecasts.csv trend_week_*.csv test_routes.csv
```

### Temporary/Utility Scripts
```bash
# One-time utility scripts no longer needed
consolidate_scripts.sh                          # One-time consolidation
organize_scripts.txt                            # Planning notes
week51_auto_complete.sh                         # One-time automation
deployment_summary.txt                          # Old deployment notes
cleanup_repo.sh                                 # Old cleanup script (we have new plan)

# Command to remove:
rm consolidate_scripts.sh organize_scripts.txt week51_auto_complete.sh deployment_summary.txt cleanup_repo.sh
```

### Old/Obsolete Scripts
```bash
# Superseded by run_comprehensive_update.py
calculate_forecast_variance.py                  # Old variance calculator
compare_forecast_to_actual.py                   # Old comparison script
forecast_multi_week.py                          # Old multi-week script
generate_production_forecast.py                 # Superseded by comprehensive update
setup_local_adaptive_system.py                  # Old local adaptive setup
sunday_weekly_update.sh                         # Old weekly update script
run_forecast.sh                                 # Old run script

# Command to remove:
rm calculate_forecast_variance.py compare_forecast_to_actual.py forecast_multi_week.py \\
   generate_production_forecast.py setup_local_adaptive_system.py sunday_weekly_update.sh run_forecast.sh
```

---

## 📁 Files to MOVE to archive/

### Historical Documentation (Keep for reference but move)
```bash
# Move old documentation to archive
mv CURSOR_SETUP.md archive/docs/
mv ENSEMBLE_FINDINGS.md archive/docs/
mv FINAL_RECOMMENDATION.md archive/docs/
mv FORECASTING_LOGIC_REQUIRED.md archive/docs/
mv LOCAL_ADAPTIVE_README.md archive/docs/
mv LOCAL_TESTING_GUIDE.md archive/docs/
mv MODEL_1_BASELINE.md archive/docs/
mv MODEL_2_TREND.md archive/docs/
mv MODEL_3_INTEGRATED.md archive/docs/
mv MODELS_GUIDE.md archive/docs/
mv NOTEBOOK_SETUP.md archive/docs/
mv QUICK_START_GUIDE.md archive/docs/
mv QUICKSTART.md archive/docs/  # Duplicate of QUICK_START_GUIDE
mv READY_TO_RUN.md archive/docs/
mv REPO_STRUCTURE.md archive/docs/  # Outdated structure doc
mv SUNDAY_WORKFLOW_WEEKLY_UPDATES.md archive/docs/
mv SUNDAY_WORKFLOW.md archive/docs/
mv THREE_MODELS_SUMMARY.md archive/docs/
mv VARIANCE_AND_MULTIWEEK_GUIDE.md archive/docs/

# Create archive subdirectory first
mkdir -p archive/docs
```

### Old Source Files (Keep for reference)
```bash
# Move old/unused src files to archive
mkdir -p archive/src

# These are experimental or old versions - not used in current system
mv src/analyze_ensemble_routing.py archive/src/
mv src/forecast_baseline.py archive/src/
mv src/forecast_ensemble.py archive/src/
mv src/forecast_final.py archive/src/
mv src/forecast_hybrid.py archive/src/
mv src/forecast_improved.py archive/src/
mv src/forecast_integrated.py archive/src/
mv src/forecast_lane_adaptive.py archive/src/
mv src/forecast_ml.py archive/src/
mv src/forecast_multi_model_backtest.py archive/src/
mv src/forecast_optimal.py archive/src/
mv src/forecast_trend.py archive/src/
mv src/performance_tracker.py archive/src/
mv src/train_meta_model.py archive/src/
mv src/visualize_model_performance.py archive/src/

# KEEP in src/:
# - forecast_comprehensive_all_models.py (THE ONE WE USE!)
# - __init__.py
```

---

## ✅ Files to KEEP (Essential)

### Root Directory - Keep These
```
✅ README.md                                    # Main project overview
✅ requirements.txt                             # Python dependencies
✅ .gitignore                                   # Git configuration
✅ .env.example                                 # Environment template
✅ run_comprehensive_update.py                  # MAIN PRODUCTION SCRIPT
✅ model_meta_analysis.py                       # Performance tracking
```

### Documentation - Keep These (Move to docs/ folder)
```bash
# Create docs folder and organize
mkdir -p docs

# Move current documentation to docs/
mv FORECASTING_SYSTEM_JOURNEY.md docs/
mv FORECASTING_PRESENTATION.md docs/
mv ORCHESTRATION_GUIDE_BUSINESS.md docs/
mv SYSTEM_IMPROVEMENTS.md docs/
mv WEEKLY_UPDATE_GUIDE.md docs/
mv FILE_ORGANIZATION.md docs/
mv OUTPUT_ORGANIZATION_SUMMARY.md docs/
mv REPO_CLEANUP_PLAN.md docs/  # This file
```

### Source Code - Keep This
```
src/
├── __init__.py                                # Keep
└── forecast_comprehensive_all_models.py       # Keep - THE CORE MODEL FILE
```

### Folders - Keep These
```
✅ data/                                        # All outputs
✅ notebooks/                                   # Jupyter notebooks
✅ models/                                      # ML model artifacts (if used)
✅ venv/                                        # Python environment
✅ archive/                                     # Historical files
✅ .git/                                        # Git repository
```

---

## 🎯 Proposed Final Structure

```
hassett-forecasting/
│
├── README.md                                   # Project overview
├── requirements.txt                            # Dependencies
├── .gitignore                                  # Git config
├── .env.example                                # Environment template
│
├── run_comprehensive_update.py                 # 🌟 MAIN SCRIPT
├── model_meta_analysis.py                      # 🌟 PERFORMANCE TRACKING
│
├── docs/                                       # 📖 ALL DOCUMENTATION
│   ├── FORECASTING_SYSTEM_JOURNEY.md          # Complete story
│   ├── FORECASTING_PRESENTATION.md            # Slide deck
│   ├── ORCHESTRATION_GUIDE_BUSINESS.md        # Team training
│   ├── SYSTEM_IMPROVEMENTS.md                  # Improvements log
│   ├── WEEKLY_UPDATE_GUIDE.md                  # How-to guide
│   ├── FILE_ORGANIZATION.md                    # File structure
│   ├── OUTPUT_ORGANIZATION_SUMMARY.md          # Output guide
│   └── REPO_CLEANUP_PLAN.md                    # This file
│
├── src/                                        # 💻 SOURCE CODE
│   ├── __init__.py
│   └── forecast_comprehensive_all_models.py    # 14 model implementations
│
├── notebooks/                                  # 📓 JUPYTER NOTEBOOKS
│   └── 99_comprehensive_weekly_update.ipynb
│
├── data/                                       # 📊 ALL OUTPUTS (git-ignored)
│   ├── forecasts/                             # Production forecasts
│   ├── comprehensive/                          # Full comparisons
│   ├── routing_tables/                         # Model routing
│   ├── performance/                            # Performance tracking
│   ├── actuals/                               # Cached actuals
│   └── historical/                             # Historical data
│
├── archive/                                    # 🗄️ HISTORICAL (git-ignored)
│   ├── docs/                                  # Old documentation
│   └── src/                                   # Old source files
│
├── venv/                                       # 🐍 PYTHON ENV (git-ignored)
└── .git/                                       # Git repository
```

---

## 📝 Cleanup Commands

### Step 1: Create Directories
```bash
mkdir -p docs
mkdir -p archive/docs
mkdir -p archive/src
```

### Step 2: Move Documentation
```bash
# Move current docs to docs/
mv FORECASTING_SYSTEM_JOURNEY.md docs/
mv FORECASTING_PRESENTATION.md docs/
mv ORCHESTRATION_GUIDE_BUSINESS.md docs/
mv SYSTEM_IMPROVEMENTS.md docs/
mv WEEKLY_UPDATE_GUIDE.md docs/
mv FILE_ORGANIZATION.md docs/
mv OUTPUT_ORGANIZATION_SUMMARY.md docs/

# Move old docs to archive
mv CURSOR_SETUP.md ENSEMBLE_FINDINGS.md FINAL_RECOMMENDATION.md archive/docs/
mv FORECASTING_LOGIC_REQUIRED.md LOCAL_ADAPTIVE_README.md LOCAL_TESTING_GUIDE.md archive/docs/
mv MODEL_1_BASELINE.md MODEL_2_TREND.md MODEL_3_INTEGRATED.md archive/docs/
mv MODELS_GUIDE.md NOTEBOOK_SETUP.md QUICK_START_GUIDE.md QUICKSTART.md archive/docs/
mv READY_TO_RUN.md REPO_STRUCTURE.md archive/docs/
mv SUNDAY_WORKFLOW_WEEKLY_UPDATES.md SUNDAY_WORKFLOW.md THREE_MODELS_SUMMARY.md archive/docs/
mv VARIANCE_AND_MULTIWEEK_GUIDE.md archive/docs/
```

### Step 3: Move Old Source Files
```bash
# Move experimental/old src files to archive
mv src/analyze_ensemble_routing.py archive/src/
mv src/forecast_baseline.py archive/src/
mv src/forecast_ensemble.py archive/src/
mv src/forecast_final.py archive/src/
mv src/forecast_hybrid.py archive/src/
mv src/forecast_improved.py archive/src/
mv src/forecast_integrated.py archive/src/
mv src/forecast_lane_adaptive.py archive/src/
mv src/forecast_ml.py archive/src/
mv src/forecast_multi_model_backtest.py archive/src/
mv src/forecast_optimal.py archive/src/
mv src/forecast_trend.py archive/src/
mv src/performance_tracker.py archive/src/
mv src/train_meta_model.py archive/src/
mv src/visualize_model_performance.py archive/src/
```

### Step 4: Delete Obsolete Files
```bash
# Delete old data files
rm comprehensive_week51.csv routes_week_51.csv week_51_forecasts.csv
rm trend_week_50_2025_20251212_141141.csv test_routes.csv

# Delete temporary scripts
rm consolidate_scripts.sh organize_scripts.txt week51_auto_complete.sh
rm deployment_summary.txt cleanup_repo.sh

# Delete obsolete scripts
rm calculate_forecast_variance.py compare_forecast_to_actual.py
rm forecast_multi_week.py generate_production_forecast.py
rm setup_local_adaptive_system.py sunday_weekly_update.sh run_forecast.sh
```

### Step 5: Update README
```bash
# Update README.md to reflect new structure
# (Manual edit needed)
```

---

## ⚠️ Before You Delete

### Verify These Files Aren't Being Used
```bash
# Check if any script references files we're about to delete
grep -r "calculate_forecast_variance" . --exclude-dir=venv --exclude-dir=.git
grep -r "compare_forecast_to_actual" . --exclude-dir=venv --exclude-dir=.git
grep -r "generate_production_forecast" . --exclude-dir=venv --exclude-dir=.git

# If no results (or only this file), safe to delete
```

---

## 📊 Impact Summary

### Before Cleanup
```
Root directory: ~40+ files (mix of scripts, data, docs)
src/: 17 files (only 1 actively used)
Documentation: Scattered across 26 MD files
Total clutter: HIGH
```

### After Cleanup
```
Root directory: 4 files (2 scripts + README + requirements)
src/: 2 files (just what we need)
docs/: 8 organized files (current docs)
archive/: 18+ old docs, 15 old scripts (preserved but out of way)
Total clutter: MINIMAL
```

### Files Removed
- **Delete**: ~12 files (old data, temp scripts)
- **Archive**: ~33 files (old docs, old src)
- **Organize**: ~8 files (move to docs/)
- **Keep**: ~5 files (essentials only)

---

## ✅ Post-Cleanup Checklist

- [ ] Verify `run_comprehensive_update.py` still works
- [ ] Verify `model_meta_analysis.py` still works
- [ ] Check that `src/forecast_comprehensive_all_models.py` exists
- [ ] Verify `data/` folders are intact
- [ ] Update `README.md` with new structure
- [ ] Test running weekly update
- [ ] Commit changes to git

---

## 🎉 Benefits

1. **Clean Root**: Only essential files visible
2. **Organized Docs**: All documentation in `docs/`
3. **Lean Source**: Only actively used code
4. **Preserved History**: Old files in `archive/` for reference
5. **Easy Navigation**: Clear structure for team
6. **Professional**: Industry-standard organization

---

**Status:** Ready to execute
**Risk:** Low (moving to archive, not deleting important files)
**Time:** 5 minutes to execute all commands
**Recommendation:** Execute all steps in order
