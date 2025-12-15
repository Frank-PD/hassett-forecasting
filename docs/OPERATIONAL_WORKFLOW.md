# OPERATIONAL WORKFLOW - ADAPTIVE FORECASTING SYSTEM

## Overview

This document describes how to deploy and operate the adaptive ensemble forecasting system in Azure Data Factory (ADF). The system uses **route-specific model selection** to achieve 14.3% average error vs 55.8% with a single model (74% improvement).

---

## DEPLOYMENT OPTIONS

### Option 1: Static Routing (Simplest)
**Use Case:** Initial deployment, stable routes
**Maintenance:** Update quarterly or when performance degrades
**Setup Time:** 5 minutes

### Option 2: Rolling Window Retraining (Adaptive)
**Use Case:** Routes with changing patterns
**Maintenance:** Weekly retraining (14 mins runtime)
**Setup Time:** 30 minutes

### Option 3: Meta-Learning Model (Recommended)
**Use Case:** New routes, dynamic environment
**Maintenance:** Monthly meta-model retraining
**Setup Time:** 1 hour

### Option 4: Performance Tracking + Adaptive (Best)
**Use Case:** Production system with continuous improvement
**Maintenance:** Automated weekly updates
**Setup Time:** 2 hours

---

## RECOMMENDED WORKFLOW (Option 4)

### Phase 1: Initial Deployment (Week 1)

#### Step 1: Generate Initial Routing Table
```bash
# Run comprehensive comparison on historical data
python3 src/forecast_comprehensive_all_models.py \
  --week 50 \
  --year 2025 \
  --actuals "data.csv" \
  --output comprehensive_all_models_week50.csv

# Generate routing table
python3 src/analyze_ensemble_routing.py \
  --input comprehensive_all_models_week50.csv \
  --routing-table route_model_routing_table.csv \
  --summary deployment_summary.txt
```

**Output:** `route_model_routing_table.csv` with 1,487 routes

#### Step 2: Deploy to Azure Data Factory

**ADF Pipeline Components:**

1. **Lookup Activity**: Load routing table into memory
   ```json
   {
     "name": "LoadRoutingTable",
     "type": "Lookup",
     "inputs": [{
       "referenceName": "RoutingTableDataset",
       "type": "DatasetReference"
     }],
     "typeProperties": {
       "firstRowOnly": false
     }
   }
   ```

2. **ForEach Activity**: Loop through routes to forecast
   ```json
   {
     "name": "ForecastEachRoute",
     "type": "ForEach",
     "dependsOn": [{
       "activity": "LoadRoutingTable",
       "dependencyConditions": ["Succeeded"]
     }],
     "items": {
       "@activity('GetRoutesToForecast').output.value"
     },
     "activities": [...]
   }
   ```

3. **Switch Activity**: Select model based on routing table
   ```json
   {
     "name": "SelectForecastModel",
     "type": "Switch",
     "on": "@item().Optimal_Model",
     "cases": [
       {
         "value": "04_Recent_8W",
         "activities": [{"name": "Forecast_Recent_8W", ...}]
       },
       {
         "value": "18_Clustering",
         "activities": [{"name": "Forecast_Clustering", ...}]
       },
       ...
     ],
     "defaultActivities": [{
       "name": "Forecast_Default",
       "type": "DatabricksNotebook",
       "typeProperties": {
         "notebookPath": "/forecasting/04_Recent_8W"
       }
     }]
   }
   ```

4. **Databricks Notebooks**: One per model type
   - `/forecasting/01_Historical_Baseline.py`
   - `/forecasting/02_Recent_2W.py`
   - `/forecasting/04_Recent_8W.py`
   - etc.

#### Step 3: Handle New Routes

For routes NOT in routing table, use **Meta-Learning Model**:

1. **Train meta-model** (one-time):
   ```bash
   python3 src/train_meta_model.py \
     --comparison comprehensive_all_models_week50.csv \
     --historical "historical_data.csv" \
     --model-output models/meta_model.pkl \
     --features-output models/feature_columns.pkl
   ```

2. **Deploy meta-model to ADF**:
   - Upload `models/meta_model.pkl` to Azure Blob Storage
   - Load in Databricks notebook
   - Use for routes not in routing table

3. **Prediction logic**:
   ```python
   # In Databricks notebook
   import joblib

   # Load meta-model
   meta_model = joblib.load('/dbfs/mnt/models/meta_model.pkl')
   feature_cols = joblib.load('/dbfs/mnt/models/feature_columns.pkl')

   # For each new route
   def predict_best_model(route_features):
       X = route_features[feature_cols]
       predicted_model = meta_model.predict(X)[0]
       return predicted_model
   ```

---

### Phase 2: Weekly Operations

#### Week 2-4: Collect Performance Data

**Every Monday (after actual data arrives):**

```bash
# Step 1: Compare last week's forecasts to actuals
python3 src/compare_forecast_to_actual.py \
  --forecasts "forecasts_week51.csv" \
  --actuals "actuals_week51.csv" \
  --output "performance_week51.csv"

# Step 2: Record performance in tracking database
python3 src/performance_tracker.py \
  --action record \
  --week-results "performance_week51.csv" \
  --db performance_tracking.db
```

**ADF Setup:**
- Schedule: Every Monday at 6 AM
- Triggers after actual data loads
- Stores results in `performance_tracking.db` (SQL Database)

---

### Phase 3: Monthly Optimization

#### First Monday of Each Month:

```bash
# Step 1: Update routing table based on last 8 weeks performance
python3 src/performance_tracker.py \
  --action update \
  --routing-table route_model_routing_table.csv \
  --output route_model_routing_table_updated.csv \
  --lookback-weeks 8 \
  --db performance_tracking.db

# Step 2: Replace routing table in ADF
az storage blob upload \
  --account-name <storage> \
  --container forecasting \
  --name routing_table.csv \
  --file route_model_routing_table_updated.csv \
  --overwrite

# Step 3: Check performance summary
python3 src/performance_tracker.py \
  --action summary \
  --lookback-weeks 8 \
  --db performance_tracking.db
```

**This automatically:**
- Identifies routes where a different model is now performing better
- Switches routes to better-performing models
- Maintains 8-week rolling window performance
- Only switches if improvement is >5% error reduction

---

### Phase 4: Quarterly Retraining

#### First Week of Each Quarter:

```bash
# Rerun comprehensive comparison on last 12 weeks
python3 src/forecast_comprehensive_all_models.py \
  --week <current_week> \
  --year <current_year> \
  --actuals "last_12_weeks_actuals.csv" \
  --output comprehensive_quarterly.csv

# Regenerate routing table
python3 src/analyze_ensemble_routing.py \
  --input comprehensive_quarterly.csv \
  --routing-table route_model_routing_table_q1.csv

# Retrain meta-model
python3 src/train_meta_model.py \
  --comparison comprehensive_quarterly.csv \
  --historical "last_52_weeks_data.csv" \
  --model-output models/meta_model.pkl

# Deploy updated artifacts to ADF
```

**Why Quarterly?**
- Captures seasonal pattern changes
- Identifies new route behaviors
- Refreshes meta-model with recent data
- Ensures routing table stays current

---

## DECISION TREE: WHICH MODEL TO USE?

```
┌─────────────────────────────────────┐
│   New Route to Forecast (Week N)   │
└──────────────┬──────────────────────┘
               │
               ▼
         ┌─────────────┐
         │ Route in    │────── NO ───────┐
         │ Routing     │                 │
         │ Table?      │                 │
         └──────┬──────┘                 │
                │ YES                    │
                ▼                        ▼
         ┌─────────────┐          ┌─────────────┐
         │ Use         │          │ Extract     │
         │ Optimal_    │          │ Route       │
         │ Model from  │          │ Features    │
         │ Table       │          └──────┬──────┘
         └─────────────┘                 │
                                         ▼
                                  ┌─────────────┐
                                  │ Use Meta-   │
                                  │ Model to    │
                                  │ Predict     │
                                  │ Best Model  │
                                  └──────┬──────┘
                                         │
                ┌────────────────────────┴────────┐
                │                                 │
                ▼                                 ▼
         ┌─────────────┐                   ┌─────────────┐
         │ High        │                   │ Low         │
         │ Confidence? │                   │ Confidence? │
         │ (error<20%) │                   │ (error>50%) │
         └──────┬──────┘                   └──────┬──────┘
                │                                 │
                ▼                                 ▼
         Use specified                     Add confidence
         model                             warning flag
```

---

## AZURE DATA FACTORY ARCHITECTURE

### Data Flow

```
┌──────────────────┐
│  Historical Data │ (Last 52 weeks)
│  (Databricks)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      ┌──────────────────┐
│  Routing Table   │◄─────│  Monthly Update  │
│  (Blob Storage)  │      │  Pipeline        │
└────────┬─────────┘      └──────────────────┘
         │
         │ Lookup
         ▼
┌──────────────────┐
│  Daily Forecast  │
│  Pipeline        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  For Each Route  │
│  Get Model from  │
│  Routing Table   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Switch Activity │
│  Route to Correct│
│  Model Notebook  │
└────────┬─────────┘
         │
         ├───► Databricks: 01_Historical_Baseline
         ├───► Databricks: 02_Recent_2W
         ├───► Databricks: 04_Recent_8W
         ├───► Databricks: 18_Clustering
         └───► etc.

         │
         ▼
┌──────────────────┐
│  Aggregate All   │
│  Forecasts       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Output Table    │
│  (SQL Database)  │
└──────────────────┘
```

### Weekly Performance Tracking

```
┌──────────────────┐
│  Monday: Actual  │
│  Data Arrives    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Compare to Last │
│  Week's Forecast │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Calculate Errors│
│  Per Model/Route │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Store in        │
│  Performance DB  │
│  (SQL Database)  │
└──────────────────┘
```

---

## DATABASE SCHEMA

### Performance Tracking Database (SQL)

```sql
CREATE TABLE performance_history (
    id INT PRIMARY KEY IDENTITY,
    route_key NVARCHAR(255) NOT NULL,
    ODC NVARCHAR(50),
    DDC NVARCHAR(50),
    ProductType NVARCHAR(50),
    dayofweek INT,
    week_number INT NOT NULL,
    year INT NOT NULL,
    model_name NVARCHAR(100) NOT NULL,
    forecast_value FLOAT,
    actual_value FLOAT,
    error_pct FLOAT,
    absolute_error_pct FLOAT,
    timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Performance UNIQUE (route_key, week_number, year, model_name)
);

CREATE INDEX IX_Performance_Route_Week ON performance_history(route_key, week_number);
CREATE INDEX IX_Performance_Model ON performance_history(model_name);

CREATE TABLE routing_updates (
    id INT PRIMARY KEY IDENTITY,
    route_key NVARCHAR(255) NOT NULL,
    week_number INT NOT NULL,
    year INT NOT NULL,
    old_model NVARCHAR(100),
    new_model NVARCHAR(100),
    reason NVARCHAR(500),
    performance_improvement FLOAT,
    timestamp DATETIME DEFAULT GETDATE()
);
```

---

## MONITORING & ALERTS

### Key Metrics to Track

1. **Overall System Performance**
   - Average MAPE across all routes (target: <20%)
   - % routes with error <20% (target: >80%)
   - % routes with error <50% (target: >90%)

2. **Model Distribution**
   - Which models are used most frequently
   - Are all models being utilized? (if not, consider removing)

3. **Routing Table Changes**
   - How many routes switched models this month?
   - Average improvement from switches

4. **New Route Performance**
   - Meta-model prediction accuracy
   - Error rate for new routes vs known routes

### Alert Conditions

```python
# Weekly Alert Check (Monday after forecasts)
if average_mape > 25:
    ALERT("System MAPE above threshold")

if pct_routes_under_20_error < 70:
    ALERT("Too many routes with high error")

if routes_switched > 100:
    ALERT("Unusual number of routing changes - investigate")
```

---

## EXAMPLE WEEKLY TIMELINE

### Monday
- 6:00 AM: Actual data arrives
- 6:30 AM: Compare forecasts to actuals
- 7:00 AM: Record performance in database
- 7:30 AM: Send weekly performance report

### Tuesday-Friday
- Daily forecasts run at 8:00 AM using routing table

### First Monday of Month
- 8:00 AM: Update routing table based on last 8 weeks
- 9:00 AM: Deploy updated routing table
- 10:00 AM: Send routing update report

### First Week of Quarter
- Rerun comprehensive comparison
- Retrain meta-model
- Regenerate routing table
- Deploy all updated artifacts

---

## COST OPTIMIZATION

### Compute Costs

**Current:**
- Comprehensive comparison: 14 mins (1,487 routes × 18 models)
- Daily forecast with routing: ~2 mins (1,487 routes × 1 model each)

**Recommended:**
- Initial setup: Run comprehensive comparison once (1 hour Databricks cluster)
- Daily: Use routing table lookup (5 min Databricks cluster)
- Weekly: Performance tracking (2 min Databricks cluster)
- Monthly: Update routing table (5 min Databricks cluster)
- Quarterly: Retraining (1 hour Databricks cluster)

**Estimated Databricks Costs:**
- Daily: $0.50/day (5 min × $6/hour DBU rate)
- Monthly: $15/month for daily forecasts
- Quarterly: $20 for retraining
- **Total: ~$200/year**

---

## ROLLBACK PLAN

If performance degrades after routing update:

```bash
# Restore previous routing table
az storage blob download \
  --account-name <storage> \
  --container forecasting \
  --name routing_table_backup_YYYYMMDD.csv \
  --file routing_table.csv

# Upload to replace current
az storage blob upload \
  --account-name <storage> \
  --container forecasting \
  --name routing_table.csv \
  --file routing_table.csv \
  --overwrite
```

**Always:**
- Backup routing table before monthly updates
- Keep last 3 months of routing tables
- Version control all meta-models

---

## FAQ

### Q: What if a new route appears that's not in the routing table?

**A:** Use the meta-learning model to predict which forecasting model to use based on the route's characteristics (volume, volatility, trend, etc.). The meta-model was trained on 620 routes and can generalize to new routes.

### Q: How often should I retrain the meta-model?

**A:** Quarterly is recommended. The meta-model learns general patterns about when each forecasting method works well. These patterns are stable, so frequent retraining isn't necessary.

### Q: Can I use just one model instead of 18?

**A:** Yes, but you'll get 55.8% error instead of 14.3% error. Using the ensemble approach with route-specific models reduces error by 74%.

### Q: What if I don't want to track performance every week?

**A:** Use Option 1 (Static Routing Table). Deploy once, update quarterly. You'll still get 14.3% error, but won't adapt to changing patterns.

### Q: How do I know which approach (Option 1-4) to use?

**A:**
- **Start with Option 1** (Static) for initial deployment
- **Upgrade to Option 2** (Rolling) if you see pattern changes
- **Upgrade to Option 3** (Meta-Learning) when you have many new routes
- **Upgrade to Option 4** (Full Adaptive) for production systems

---

## NEXT STEPS

1. ✅ Review this workflow document
2. ✅ Choose deployment option (recommend starting with Option 1)
3. ✅ Deploy routing table to ADF (see Step 2 above)
4. ✅ Run for 4 weeks, collect performance data
5. ✅ Upgrade to Option 4 (adaptive) after validation
6. ✅ Set up monitoring and alerts
7. ✅ Schedule quarterly retraining

---

## SUPPORT

For questions or issues:
1. Review comprehensive comparison output: `comprehensive_all_models_week50.csv`
2. Check deployment summary: `deployment_summary.txt`
3. Analyze performance: `python3 src/performance_tracker.py --action summary`
4. Review visualizations in `visualizations/` folder
