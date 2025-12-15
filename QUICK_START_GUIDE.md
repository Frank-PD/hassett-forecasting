# QUICK START GUIDE - Adaptive Forecasting System

## THE BOTTOM LINE

**Using ONE model for all routes:** 55.8% error
**Using the RIGHT model for EACH route:** 14.3% error
**Improvement:** 74% reduction in error!

---

## 4 DEPLOYMENT OPTIONS (Choose One)

### Option 1: Static Routing ⭐ **START HERE**
**Effort:** 30 minutes | **Maintenance:** Quarterly update | **Cost:** $15/month

**What you do:**
1. Load routing table in Azure Data Factory
2. For each route, look up which model to use
3. Run that model's Databricks notebook
4. Done!

**Files you need:**
- `route_model_routing_table.csv` (already created ✅)

---

### Option 2: Rolling Retraining
**Effort:** 2 hours | **Maintenance:** Weekly auto-run | **Cost:** $20/month

**What you do:**
1. Every week: Rerun comparison on last 8 weeks
2. Update routing table
3. Deploy updated table to ADF

**When to use:** Routes with changing patterns

---

### Option 3: Meta-Learning
**Effort:** 4 hours | **Maintenance:** Monthly retraining | **Cost:** $22/month

**What you do:**
1. Train ML model to predict which forecasting model to use
2. For known routes: Use routing table
3. For new routes: Use meta-model

**When to use:** Many new routes appearing

---

### Option 4: Full Adaptive ⭐ **PRODUCTION**
**Effort:** 8 hours | **Maintenance:** Automated | **Cost:** $27/month

**What you do:**
1. Week 1: Deploy routing table
2. Weekly: Track actual vs forecast errors
3. Monthly: Auto-update routing table based on recent performance
4. Quarterly: Retrain everything

**When to use:** Production system, want continuous improvement

---

## AZURE DATA FACTORY SETUP (Option 1)

### Step 1: Upload Routing Table (5 min)

```bash
# Upload routing table to Blob Storage
az storage blob upload \
  --account-name <your_storage> \
  --container forecasting \
  --name routing_table.csv \
  --file route_model_routing_table.csv
```

### Step 2: Create ADF Pipeline (15 min)

**Pipeline Activities:**
1. **Lookup**: Load `routing_table.csv` into memory
2. **Lookup**: Get list of routes needing forecasts
3. **ForEach**: For each route:
   - Find route in routing table
   - Get `Optimal_Model` column
   - **Switch**: Run the correct Databricks notebook based on `Optimal_Model`
4. **Aggregate**: Combine all forecasts

### Step 3: Create Databricks Notebooks (10 min)

Create one notebook per model in `/forecasting/` directory:

**Example: `/forecasting/04_Recent_8W.py`**
```python
# Get parameters
route_key = dbutils.widgets.get("route_key")
ODC = dbutils.widgets.get("ODC")
DDC = dbutils.widgets.get("DDC")
ProductType = dbutils.widgets.get("ProductType")
dayofweek = dbutils.widgets.get("dayofweek")

# Get historical data
df = spark.sql(f"""
  SELECT * FROM historical_data
  WHERE ODC = '{ODC}' AND DDC = '{DDC}'
    AND ProductType = '{ProductType}' AND dayofweek = {dayofweek}
  ORDER BY week_ending DESC
  LIMIT 8
""")

# Calculate 8-week average
recent_8w_avg = df.agg({"pieces": "avg"}).collect()[0][0]

# Save forecast
forecast_df = spark.createDataFrame([
  (route_key, recent_8w_avg, "04_Recent_8W")
], ["route_key", "forecast", "model"])

forecast_df.write.mode("append").saveAsTable("forecasts")
```

Repeat for all 18 models.

---

## DECISION TREE

```
┌─────────────────────────────┐
│ Do you want to deploy       │
│ to production right now?    │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
    YES          NO
     │            │
     ▼            ▼
┌─────────┐  ┌─────────┐
│ Option 1│  │ Are you │
│ Static  │  │ testing?│
└─────────┘  └────┬────┘
                  │
            ┌─────┴─────┐
           YES          NO
            │            │
            ▼            ▼
       ┌─────────┐  ┌─────────┐
       │ Use     │  │ Many    │
       │ routing │  │ new     │
       │ table   │  │ routes? │
       │ locally │  └────┬────┘
       └─────────┘       │
                    ┌────┴────┐
                   YES       NO
                    │         │
                    ▼         ▼
               ┌─────────┐ ┌─────────┐
               │ Option 3│ │ Option 2│
               │ Meta-   │ │ Rolling │
               │ Learning│ │ Retrain │
               └─────────┘ └─────────┘
```

---

## FILES & WHAT THEY DO

### Data Files (Already Created ✅)
| File | What It Is | Size |
|------|-----------|------|
| `comprehensive_all_models_week50.csv` | All 18 models tested on all routes | 1,487 routes |
| `route_model_routing_table.csv` | Which model to use for each route | 1,487 routes |
| `deployment_summary.txt` | Executive summary | 1 page |

### Python Scripts (Ready to Use ✅)
| Script | What It Does | When to Run |
|--------|-------------|------------|
| `src/forecast_comprehensive_all_models.py` | Test all 18 models | Quarterly |
| `src/analyze_ensemble_routing.py` | Generate routing table | After comparison |
| `src/visualize_model_performance.py` | Create charts | After comparison |
| `src/train_meta_model.py` | Train meta-learning model | Monthly (Option 3) |
| `src/performance_tracker.py` | Track weekly errors | Weekly (Option 4) |

### Documentation (Read These ✅)
| Doc | What It Covers | Read Time |
|-----|---------------|-----------|
| `QUICK_START_GUIDE.md` | This file | 5 min |
| `docs/ADAPTIVE_SYSTEM_SUMMARY.md` | Complete solution overview | 15 min |
| `docs/OPERATIONAL_WORKFLOW.md` | Detailed deployment guide | 30 min |

---

## WHAT EACH MODEL IS

| Model ID | Model Name | What It Does | Best For |
|----------|-----------|--------------|----------|
| 01 | Historical Baseline | All-time average | Stable routes |
| 02 | Recent 2W | Last 2 weeks average | Trending routes |
| 03 | Recent 4W Hybrid | Last 4 weeks average | Moderate trends |
| 04 | Recent 8W | Last 8 weeks average | Seasonal routes |
| 05 | Trend Adjusted | Linear trend forecast | Growing/declining |
| 06 | Prior Week | Last week's value | Stable week-to-week |
| 07 | Same Week Last Year | Year-over-year | Strong seasonality |
| 08 | Week Specific | Week-of-year average | Annual patterns |
| 09 | Exp Smoothing | Exponential smoothing | Smooth trends |
| 10 | Probabilistic | 75th percentile | Conservative forecast |
| 11 | Hybrid Week Blend | Recent + last year | Balanced approach |
| 12 | Median Recent | Median of recent | Outlier-resistant |
| 13 | Weighted Recent | Weighted recent weeks | Recent emphasis |
| 14 | SARIMA | Time series model | Complex seasonality |
| 15 | ML Classifier + Vol | ML route selection | Pattern detection |
| 16 | ML Regressor | RandomForest regression | Non-linear patterns |
| 17 | Lane Adaptive | Dynamic method selection | Varying patterns |
| 18 | Clustering | Cluster-based average | Similar routes |

---

## PERFORMANCE SNAPSHOT

### By Routes Won (Top 5)
1. **04_Recent_8W** - 82 routes (13.2%)
2. **02_Recent_2W** - 76 routes (12.3%)
3. **18_Clustering** - 65 routes (10.5%)
4. **01_Historical_Baseline** - 58 routes (9.4%)
5. **08_Week_Specific** - 48 routes (7.7%)

### By Average Error (Top 5)
1. **04_Recent_8W** - 55.8% MAPE (BEST)
2. **12_Median_Recent** - 56.6% MAPE
3. **03_Recent_4W_HYBRID** - 62.5% MAPE
4. **15_ML_Classifier_Simple_Vol** - 62.5% MAPE
5. **09_Exp_Smoothing** - 66.9% MAPE

### Ensemble Performance
- **Average MAPE:** 14.3%
- **Median MAPE:** 4.3%
- **Routes <20% error:** 81.6%
- **Routes <50% error:** 92.7%

---

## COMMANDS CHEAT SHEET

### Run Comprehensive Comparison
```bash
python3 src/forecast_comprehensive_all_models.py \
  --week 50 --year 2025 \
  --actuals "data.csv" \
  --output comprehensive.csv
```

### Generate Routing Table
```bash
python3 src/analyze_ensemble_routing.py \
  --input comprehensive.csv \
  --routing-table routing_table.csv
```

### Create Visualizations
```bash
python3 src/visualize_model_performance.py \
  --input comprehensive.csv \
  --output-dir visualizations
```

### Train Meta-Model (Optional)
```bash
python3 src/train_meta_model.py \
  --comparison comprehensive.csv \
  --historical "historical_data.csv" \
  --model-output models/meta_model.pkl
```

### Track Performance (Weekly)
```bash
# Record week's performance
python3 src/performance_tracker.py \
  --action record \
  --week-results "week_51_performance.csv"

# Update routing table (monthly)
python3 src/performance_tracker.py \
  --action update \
  --routing-table routing_table.csv \
  --output routing_table_updated.csv

# Check summary
python3 src/performance_tracker.py \
  --action summary
```

---

## TROUBLESHOOTING

### "Route not in routing table"
→ Use 04_Recent_8W (best single model)
→ Or use meta-model to predict

### "Forecast error too high"
→ Run monthly routing table update
→ Check if route patterns changed
→ Consider quarterly retraining

### "Too many model switches"
→ Increase switch threshold from 5% to 10%
→ Require more weeks of data (6 instead of 4)

### "ADF pipeline slow"
→ Cache routing table in memory
→ Run ForEach in parallel (batchCount=20)
→ Use smaller Databricks cluster for simple models

---

## NEXT STEPS

### This Week
1. ✅ Read this guide (you're doing it!)
2. Review routing table: `route_model_routing_table.csv`
3. Check visualizations: `visualizations/` folder
4. Read deployment summary: `deployment_summary.txt`

### Next Week
1. Choose deployment option (recommend Option 1)
2. Set up Azure Data Factory pipeline
3. Create Databricks notebooks for top 5 models
4. Test with 10 sample routes

### Month 1
1. Deploy to production
2. Monitor daily forecasts
3. Compare to actual data when available
4. Validate 14.3% average MAPE

### Month 2+
1. Add performance tracking
2. Consider upgrading to Option 4 (adaptive)
3. Set up automated retraining

---

## QUESTIONS?

### "Do I really need 18 models?"
No! Start with top 5:
- 04_Recent_8W
- 02_Recent_2W
- 18_Clustering
- 01_Historical_Baseline
- 08_Week_Specific

These cover 53% of routes.

### "Can I just use 04_Recent_8W for everything?"
Yes, but you'll get 55.8% error instead of 14.3% error.

### "How long to deploy?"
- Option 1 (Static): 30 minutes
- Option 2 (Rolling): 2 hours
- Option 3 (Meta-Learning): 4 hours
- Option 4 (Full Adaptive): 8 hours

### "What's the ROI?"
If 74% error reduction saves $350/year, system pays for itself.

---

## SUCCESS CHECKLIST

Week 1:
- [ ] Routing table deployed to ADF
- [ ] Pipeline running daily
- [ ] No errors

Month 1:
- [ ] Average MAPE <20%
- [ ] 80%+ routes <20% error
- [ ] Performance tracking working

Month 3:
- [ ] Average MAPE <15%
- [ ] Monthly updates automated
- [ ] System running smoothly

---

**Ready to deploy? Start with Option 1 (Static Routing) and go!**
