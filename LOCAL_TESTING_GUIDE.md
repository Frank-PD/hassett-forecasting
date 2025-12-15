# LOCAL TESTING GUIDE

## Quick Start - Test The System Locally (5 Minutes)

Before deploying to Azure Data Factory, you want to test everything works correctly on your local machine. Here's how:

---

## STEP-BY-STEP LOCAL TESTING

### Step 1: Prepare Test Routes (30 seconds)

```bash
# Extract 50 sample routes from routing table for testing
python3 prepare_test_routes.py \
  --routing-table route_model_routing_table.csv \
  --num-routes 50 \
  --output test_routes.csv
```

**Output:** `test_routes.csv` with 50 routes to forecast

**What this does:** Extracts a random sample of 50 routes from your routing table to test with.

---

### Step 2: Run Local Forecast (2-3 minutes)

```bash
# Run forecasts locally using the routing table
python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast test_routes.csv \
  --actuals "/Users/frankgiles/Downloads/data 4.csv" \
  --output local_forecasts_test.csv \
  --week 51 \
  --year 2025
```

**Output:** `local_forecasts_test.csv` with forecasts for all 50 routes

**What this does:**
1. Loads the routing table
2. For each of the 50 test routes:
   - Looks up which model to use in the routing table
   - Gets historical data for that route
   - Runs the optimal model
   - Generates forecast
3. Compares forecasts to actuals
4. Shows performance metrics

---

### Step 3: Review Results (1 minute)

```bash
# View the forecast results
head -20 local_forecasts_test.csv

# Or open in Excel/Numbers
open local_forecasts_test.csv
```

**Expected columns in output:**
- `route_key` - Route identifier
- `ODC`, `DDC`, `ProductType`, `dayofweek` - Route details
- `week_number`, `year` - Forecast period
- `optimal_model` - Which model was used
- `forecast` - Forecasted volume
- `confidence` - HIGH/MEDIUM/LOW based on historical error
- `historical_error_pct` - Historical error for this model/route
- `actual` - Actual volume (if available)
- `error_pct` - Forecast error %
- `absolute_error_pct` - Absolute forecast error %

---

## WHAT TO EXPECT

### Normal Output

```
================================================================================
LOCAL FORECAST RUNNER
================================================================================

📂 Loading routing table: route_model_routing_table.csv
   ✅ Loaded 1,487 routes

📂 Loading historical data: data.csv
   ✅ Loaded 871 historical records

📊 Model Distribution in Routing Table:
   01_Historical_Baseline                     821 routes ( 55.2%)
   02_Recent_2W                                98 routes (  6.6%)
   04_Recent_8W                                94 routes (  6.3%)
   ...

📊 Forecasting 50 routes...
   Progress: 50/50 routes...

✅ Generated 50 forecasts

📊 Models Used:
   01_Historical_Baseline                      25 routes
   02_Recent_2W                                 6 routes
   04_Recent_8W                                 4 routes
   ...

📊 Comparison Results (22 routes with actuals):
   Average MAPE: 14.3%         <-- TARGET
   Median MAPE: 4.3%
   Routes <20% error: 81.6%    <-- GOOD
   Routes <50% error: 92.7%    <-- VERY GOOD

✅ LOCAL FORECAST COMPLETE
```

### Performance Targets

| Metric | Target | What It Means |
|--------|--------|---------------|
| Average MAPE | <20% | Overall forecast accuracy |
| Median MAPE | <10% | Typical forecast accuracy |
| Routes <20% error | >75% | Most routes forecasted well |
| Routes <50% error | >90% | Very few bad forecasts |

---

## COMMON ISSUES & FIXES

### Issue 1: "Route not in routing table"

**Message:**
```
⚠️ Route LAX-SFO-PKG-1 not in routing table, using default model
```

**What it means:** The test route doesn't exist in your routing table

**Fix:** This is normal if testing with random routes. The system will use the best single model (04_Recent_8W) as default.

**For production:** Every route should be in routing table, or use meta-model for new routes.

---

### Issue 2: "No historical data for route"

**Message:**
```
⚠️  Error running 04_Recent_8W: not enough historical data
```

**What it means:** The route has no historical shipments

**Fix:** The system will return 0 forecast for routes with no history. This is expected for new/inactive routes.

**For production:** Filter out inactive routes, or use minimum volume threshold.

---

### Issue 3: MAPE much higher than 14.3%

**Possible causes:**
1. Testing with routes that have sparse/volatile data
2. Test routes don't match routing table routes
3. Historical data is incomplete

**Fix:**
```bash
# Test with ALL routes instead of random sample
python3 prepare_test_routes.py \
  --routing-table route_model_routing_table.csv \
  --num-routes 0 \
  --output all_routes.csv

python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "data.csv" \
  --routes-to-forecast all_routes.csv \
  --actuals "data.csv" \
  --output all_forecasts.csv
```

This should give MAPE close to 14.3% since you're using the same routes that the routing table was built from.

---

## TESTING SCENARIOS

### Scenario 1: Quick Smoke Test (2 min)
**Goal:** Verify system works

```bash
python3 prepare_test_routes.py --num-routes 10 --output quick_test.csv
python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "data.csv" \
  --routes-to-forecast quick_test.csv \
  --output quick_forecast.csv
```

**Success criteria:** No errors, forecasts generated

---

### Scenario 2: Full Validation (5 min)
**Goal:** Verify forecasts match expected 14.3% MAPE

```bash
python3 prepare_test_routes.py --num-routes 0 --output all_routes.csv
python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "data.csv" \
  --routes-to-forecast all_routes.csv \
  --actuals "data.csv" \
  --output full_validation.csv
```

**Success criteria:** Average MAPE ~14.3%, 80%+ routes <20% error

---

### Scenario 3: New Week Forecast (Production Simulation)
**Goal:** Simulate forecasting for next week

```bash
# Create list of routes that need forecasting for Week 52
# (In production, this would come from your database)

python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "data.csv" \
  --routes-to-forecast production_routes_week52.csv \
  --output forecasts_week52.csv \
  --week 52 \
  --year 2025
```

**Success criteria:** Forecasts generated for all routes, no errors

---

## FILE FORMATS

### Input: routes_to_forecast.csv
```csv
ODC,DDC,ProductType,dayofweek
LAX,SFO,Package,1
NYC,BOS,Document,5
CHI,DET,Package,3
```

**Required columns:**
- `ODC` - Origin Distribution Center
- `DDC` - Destination Distribution Center
- `ProductType` - Product type (e.g., Package, Document, MAX, EXP)
- `dayofweek` - Day of week (1=Monday, 7=Sunday)

---

### Output: forecasts.csv
```csv
route_key,ODC,DDC,ProductType,dayofweek,week_number,year,optimal_model,forecast,confidence,historical_error_pct,actual,error_pct,absolute_error_pct
LAX-SFO-Package-1,LAX,SFO,Package,1,51,2025,04_Recent_8W,45.2,HIGH,5.2,47.0,3.8,3.8
NYC-BOS-Document-5,NYC,BOS,Document,5,51,2025,18_Clustering,12.1,HIGH,8.1,13.0,6.9,6.9
```

**Columns:**
- `route_key` - Unique route identifier
- `ODC`, `DDC`, `ProductType`, `dayofweek` - Route details
- `week_number`, `year` - Forecast period
- `optimal_model` - Which forecasting model was used
- `forecast` - Forecasted volume
- `confidence` - HIGH/MEDIUM/LOW/NEW_ROUTE
- `historical_error_pct` - Historical error for this model/route
- `actual` - Actual volume (only if actuals provided)
- `error_pct` - Forecast error % (only if actuals provided)
- `absolute_error_pct` - Absolute error % (only if actuals provided)

---

## NEXT STEPS AFTER LOCAL TESTING

### If tests pass (MAPE ~14.3%, no errors):
1. ✅ System validated
2. ✅ Ready to deploy to Azure Data Factory
3. ✅ Follow `docs/OPERATIONAL_WORKFLOW.md` for ADF setup

### If tests fail:
1. Check error messages in output
2. Verify input file formats
3. Ensure historical data has correct columns
4. Try with smaller sample first (10 routes)
5. Review routing table to ensure routes exist

---

## SIMPLIFIED COMMANDS (Copy & Paste)

### Test with 50 routes:
```bash
python3 prepare_test_routes.py --num-routes 50 --output test_routes.csv && \
python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast test_routes.csv \
  --output test_forecasts.csv
```

### Test with ALL routes (full validation):
```bash
python3 prepare_test_routes.py --num-routes 0 --output all_routes.csv && \
python3 run_local_forecast.py \
  --routing-table route_model_routing_table.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast all_routes.csv \
  --actuals "/Users/frankgiles/Downloads/data 4.csv" \
  --output full_forecasts.csv
```

---

## UNDERSTANDING THE ROUTING TABLE

The `route_model_routing_table.csv` is the core of the system:

```csv
route_key,ODC,DDC,ProductType,dayofweek,Optimal_Model,Historical_Error_Pct,Confidence
LAX-SFO-PKG-1,LAX,SFO,Package,1,04_Recent_8W,5.2,HIGH
NYC-BOS-DOC-5,NYC,BOS,Document,5,18_Clustering,8.1,HIGH
```

**For each route, it tells you:**
1. Which model works best for that specific route
2. Historical error for that model on that route
3. Confidence level (HIGH/MEDIUM/LOW)

**Local testing simulates what ADF will do:**
- ADF Lookup Activity → Python loads routing table into memory
- ADF Switch Activity → Python looks up optimal model and runs it
- ADF Databricks Notebook → Python calls model function

---

## TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'forecast_comprehensive_all_models'"

**Fix:**
```bash
# Make sure you're in the project directory
cd /Users/frankgiles/Downloads/hassett-forecasting

# Run from project root
python3 run_local_forecast.py --routing-table ...
```

### Error: "FileNotFoundError: routing_table.csv not found"

**Fix:**
```bash
# Use absolute paths
python3 run_local_forecast.py \
  --routing-table /Users/frankgiles/Downloads/hassett-forecasting/route_model_routing_table.csv \
  ...
```

### Forecasts are all 0

**Causes:**
1. No historical data for those routes
2. Routes inactive (no shipments)
3. Column name mismatch in data file

**Fix:** Check that test routes exist in historical data

---

## WHAT SUCCESS LOOKS LIKE

```
✅ Generated 50 forecasts
📊 Average MAPE: 14.3%
📊 81.6% of routes <20% error
📊 92.7% of routes <50% error

Models Used:
   04_Recent_8W      12 routes
   18_Clustering     8 routes
   01_Historical     10 routes
   ...
```

**This means:** System is working correctly and ready for production!

---

## QUICK REFERENCE

| Command | Purpose | Time |
|---------|---------|------|
| `prepare_test_routes.py` | Create test route list | 30 sec |
| `run_local_forecast.py` | Generate forecasts locally | 2-5 min |
| `open forecasts.csv` | View results | 1 min |

**Total testing time:** ~5-10 minutes

**Ready to deploy?** See `docs/OPERATIONAL_WORKFLOW.md` for Azure Data Factory setup.
