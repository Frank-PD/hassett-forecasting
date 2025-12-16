# Weekly Forecast Update Guide

## Overview

Use the `99_comprehensive_weekly_update.ipynb` notebook to update all forecasting files and routing tables in one place.

## When to Run

Run this notebook **once per week** after the evaluation week is complete and actuals are available in Databricks.

Example timeline:
- **Monday, Dec 16** (Week 51 begins): Week 50 is complete and has actuals
- **Run notebook**: Evaluate week 50, generate forecast for week 51
- **Use output**: Production forecast for week 51 is ready

## Quick Start

1. Open `notebooks/99_comprehensive_weekly_update.ipynb`

2. **Weeks are calculated automatically!**
   - Evaluation Week = Last week (current week - 1)
   - Forecast Week = Current week

   Running on Dec 15, 2025:
   - Current week: 51
   - Evaluation week: 50 (has actuals)
   - Forecast week: 51

   **To override:** Manually set `EVALUATION_WEEK` and `FORECAST_WEEK` in configuration cell

3. Run all cells (Runtime → Run All)

4. Review the summary report at the end

## What Gets Updated

### Files Created/Updated:

| File | Purpose | Location |
|------|---------|----------|
| `comprehensive_all_models_week{N}.csv` | Full model comparison with actuals | Project root |
| `route_model_routing_{timestamp}.csv` | Routing table snapshot | Project root |
| `route_model_routing_table.csv` | **Current routing table** (used for next forecast) | Project root |
| `model_performance_summary_{timestamp}.json` | Model win statistics | Project root |
| `production_forecast_week{N}.csv` | Production-ready forecast | Project root |

### Data Flow:

```
Databricks (Actuals)
    ↓
Evaluate Models against Actuals
    ↓
Determine Winners per Route
    ↓
Update Routing Table
    ↓
Generate New Forecast using Winners
    ↓
Export All Files
```

## Notebook Sections

### 1. Setup and Configuration
- Configure evaluation and forecast weeks
- Set Databricks connection

### 2. Connect and Load Data
- Connect to Databricks
- Load 4 years of historical data (up to evaluation week)

### 3. Get Actuals
- Query actual shipments for evaluation week
- Aggregate by route-day

### 4. Generate Model Forecasts
- Run all models (6 core models: Historical Baseline, Recent 2W, Recent 4W, Recent 8W, Exp Smoothing, Median Recent)
- Generate forecasts for every route-day

### 5. Calculate Errors
- Compare each model's forecast to actuals
- Error calculation:
  - If Actual > 0: `|(Forecast - Actual) / Actual * 100|`
  - If Actual = 0 and Forecast > 0: `999%`
  - If Actual = 0 and Forecast = 0: `0%`

### 6. Find Winners
- Identify the model with lowest error for each route
- Create routing table mapping route → best model

### 7. Save Results
- Export comprehensive comparison CSV
- Save routing table (timestamped + current)

### 8. Performance Tracking
- Save JSON summary with model win counts
- Track which models are performing best overall

### 9. Generate Next Week Forecast
- Use routing table to select optimal model per route
- Generate forecast for upcoming week
- Calculate confidence intervals (±50% variance)

### 10. Summary Report
- Print comprehensive summary
- Show model performance
- Display forecast totals

## Interpreting Results

### Model Win Summary
```
01_Historical_Baseline: 481 wins (32.3%)
04_Recent_8W: 280 wins (18.8%)
02_Recent_2W: 137 wins (9.2%)
...
```
- Shows how many routes each model won
- Higher wins = model is performing well overall

### Forecast Confidence Levels
- **HIGH**: Historical error ≤ 20%
- **MEDIUM**: Historical error 20-50%
- **LOW**: Historical error > 50% or 999% (no actuals)

### Production Forecast
- `forecast`: Point forecast (use this for planning)
- `forecast_low`: Lower bound (forecast - 50%)
- `forecast_high`: Upper bound (forecast + 50%)

## Troubleshooting

### Issue: "No actuals found for week X"
- **Cause**: Actuals not yet loaded in Databricks
- **Fix**: Wait for data load, or check if week number is correct

### Issue: "Connection to Databricks failed"
- **Cause**: OAuth token expired or network issue
- **Fix**: Re-authenticate with Databricks

### Issue: "Model X not found"
- **Cause**: Model function not imported
- **Fix**: Check that `forecast_comprehensive_all_models.py` exists in `src/`

### Issue: "Forecast is 0 for many routes"
- **Cause**: Insufficient historical data
- **Fix**: Review data availability for those routes

## Example Output

After running the notebook, you'll see:

```
================================================================================
COMPREHENSIVE WEEKLY UPDATE COMPLETE - 20251215_143045
================================================================================

📊 Evaluation (Week 50, 2025):
  • Routes evaluated: 1,487
  • Actual pieces: 45,289
  • Models tested: 6

🏆 Top Performing Models:
  1. 04_Recent_8W: 450 wins (30.3%)
  2. 09_Exp_Smoothing: 320 wins (21.5%)
  3. 02_Recent_2W: 280 wins (18.8%)
  4. 12_Median_Recent: 215 wins (14.5%)
  5. 01_Historical_Baseline: 180 wins (12.1%)

📈 Forecast (Week 51, 2025):
  • Routes forecasted: 1,487
  • Total forecast: 42,150 pieces
  • Forecast range: 21,075 - 63,225

  By Product Type:
    • MAX: 28,450 pieces
    • EXP: 13,700 pieces

💾 Files Generated:
  • comprehensive_all_models_week50.csv
  • route_model_routing_20251215_143045.csv
  • route_model_routing_table.csv
  • model_performance_summary_20251215_143045.json
  • production_forecast_week51.csv

================================================================================
✅ ALL UPDATES COMPLETE!
================================================================================
```

## Best Practices

1. **Run weekly** after actuals are available
2. **Review the summary** before using forecasts
3. **Check confidence levels** - LOW confidence routes need manual review
4. **Compare week-over-week** - Look for sudden changes in model performance
5. **Archive old files** - Keep timestamped files for audit trail

## Next Steps

After running the notebook:
1. Review `production_forecast_week{N}.csv`
2. Share forecast with stakeholders
3. Monitor actual vs forecast throughout the week
4. Repeat next week with updated actuals

## Questions?

- Check model implementation in `src/forecast_comprehensive_all_models.py`
- Review historical experiments in `docs/META_ANALYSIS_100_EXPERIMENTS.md`
- Examine error calculations in Step 4 of the notebook
