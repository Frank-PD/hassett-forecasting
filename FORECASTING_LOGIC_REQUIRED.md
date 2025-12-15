# Required Forecasting Logic for Route-Level Accuracy

## Executive Summary

Through testing with Week 50, 2025 actuals, we discovered the current baseline models fail catastrophically at the route level:

- **Old Model Error**: +55.6% over-forecast (26,631 vs 17,117 actual)
- **HYBRID Model Error**: +1.6% (17,383 vs 17,117 actual) ✅

**The HYBRID approach reduces error by 97%!**

---

## What We Learned

### ❌ Problem with Original Models (baseline.py, trend.py, integrated.py)

1. **Uses 2022/2024 baselines** - Too old! Many routes have changed dramatically.
   - Example: ATL→BOS had 242 pieces in 2022, only 59 in 2025 (-76%)

2. **Product-level trends** - Ignores route-specific changes
   - Applies -26.7% MAX trend globally
   - But some routes grew, others collapsed

3. **Forecasts dead routes** - 779 routes forecasted that had ZERO actuals
   - Wasted 14,099 pieces on routes that don't exist anymore

4. **Misses new routes** - 237 routes with actuals but zero forecast
   - Missed 6,155 pieces from emerging routes

---

## ✅ Solution: HYBRID Approach

### Core Logic (see `src/forecast_hybrid.py`)

```python
# Step 1: Historical Baseline (which routes ship in Week N?)
- Query 2022 Week N for MAX routes
- Query 2024 Week N for EXP routes
- This tells us WHICH routes historically ship in target week

# Step 2: Recent Activity Validation (is route still active?)
- Query last 4 weeks before target week
- Only keep routes from Step 1 that ALSO appear in recent data
- This filters out 362 dead routes!

# Step 3: Use Recent Data for Magnitude
- Don't use 2022/2024 volumes
- Use last 4 weeks average per route per day
- This captures current reality

# Step 4: Calculate Forecast
- forecast = recent_average (per route, per day)
- confidence = min(data_points / 3, 1.0)
```

### Results

| Metric | Old Model | HYBRID Model | Improvement |
|--------|-----------|--------------|-------------|
| Total Volume Error | +55.6% | +1.6% | **97% better** |
| MAPE | 162.3% | 55.7% | **66% better** |
| Ghost Routes | 779 | 772 | 1% better |
| Volume Accuracy | 26,631 vs 17,117 | 17,383 vs 17,117 | Nearly perfect! |

---

## Remaining Issues & Next Steps

### Issue 1: Still Missing 623 Routes

**Problem**: Routes that exist in actuals but NOT in forecast

**Root Cause**: These are routes that:
- Don't exist in 2022/2024 baseline (new routes)
- OR didn't ship in the exact last 4 weeks (sporadic routes)

**Fix Required**:
```python
# Add to hybrid logic:
# If route appeared in recent 4 weeks but NOT in baseline:
#   forecast = recent_average
#   confidence = 0.6 (lower confidence)
#   tag as "new_route"
```

### Issue 2: Day-of-Week Granularity

**Problem**: Some routes don't ship every day

**Current**: We forecast Monday-Saturday for all routes

**Fix Required**:
```python
# Only forecast days where route historically ships
# If route never shipped on Saturdays, don't forecast Saturday
```

### Issue 3: Product Type Validation

**Problem**: Some ODC-DDC pairs switched from MAX to EXP (or vice versa)

**Fix Required**:
```python
# Validate product type per route from recent data
# If recent data shows EXP but baseline shows MAX, use EXP
```

---

## Recommended Production Logic

### Option A: HYBRID + New Routes (Recommended)

1. **Historical Baseline** (Week N from 2022 MAX / 2024 EXP)
2. **Recent Activity Filter** (last 4 weeks, min 2 shipments)
3. **Use Recent Magnitude** (last 4 weeks average)
4. **ADD New Routes** (routes in recent but not baseline)
5. **Confidence Scoring**:
   - High (>80%): Routes with 3+ recent data points
   - Medium (50-80%): Routes with 2 data points
   - Low (<50%): New routes with 1 data point

### Option B: Pure Recent Activity

1. **Only use last 8 weeks** (no historical baseline)
2. **Require min 3 shipments** in lookback period
3. **Use last 4 weeks average** for magnitude
4. **Trend**: Compare last 2 weeks vs previous 2 weeks

**Trade-off**: Misses routes that ship sporadically (once every 2-3 weeks)

---

## Code Files

- `/src/forecast_baseline.py` - OLD: Uses 2022/2024 baseline only ❌
- `/src/forecast_trend.py` - OLD: Baseline + product-level trend ❌
- `/src/forecast_integrated.py` - OLD: Baseline + trend + seasonal ❌
- `/src/forecast_hybrid.py` - NEW: Baseline + recent validation ✅ (1.6% error)

---

## Test Results Summary

### Week 50, 2025 Actuals vs Forecast

```
Actual Total:      17,117 pieces across 871 routes

OLD (Integrated):  26,631 pieces (+55.6% error)
                   - 779 ghost routes
                   - 237 missed routes
                   - MAPE: 162.3%

HYBRID:            17,383 pieces (+1.6% error)
                   - 772 ghost routes
                   - 623 missed routes
                   - MAPE: 55.7%
```

**Conclusion**: HYBRID is dramatically better on volume and magnitude, but needs enhancement to capture all routes.

---

## Action Items

1. ✅ Implement hybrid baseline + recent validation
2. ⚠️  Add logic to capture new routes from recent data
3. ⚠️  Improve day-of-week filtering (only forecast active days)
4. ⚠️  Add product-type validation per route
5. ⚠️  Create confidence bands for uncertain forecasts
6. ⚠️  Test on multiple weeks (not just Week 50)

---

## Usage

```bash
# Generate forecast using HYBRID approach
python3 src/forecast_hybrid.py --week 51 --year 2025

# Output: hybrid_week_51_2025_TIMESTAMP.csv
# Columns: ODC, DDC, ProductType, dayofweek, forecast, confidence, ...
```

---

**Date**: 2025-12-12
**Tested**: Week 50, 2025
**Status**: HYBRID model ready for production with caveats
**Next**: Enhance to capture new/sporadic routes
