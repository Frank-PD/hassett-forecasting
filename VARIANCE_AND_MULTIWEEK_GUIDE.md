# VARIANCE & MULTI-WEEK FORECASTING GUIDE

## Overview

Two powerful additions to the forecasting system:
1. **Confidence Intervals** - Add variance ranges to forecasts (±X pieces)
2. **6-Week Outlook** - Forecast multiple weeks ahead with increasing variance

---

## 1. CONFIDENCE INTERVALS / VARIANCE

### Why This Matters

Instead of:
```
Route LAX-SFO: Forecast = 45 pieces
```

You get:
```
Route LAX-SFO: Forecast = 45 pieces [43 - 47 pieces] ±2 pieces (±4.4%)
Confidence: HIGH
```

**Use for:**
- Capacity planning (need to handle 43-47 pieces, not just 45)
- Buffer stock calculations
- Risk assessment
- Resource allocation

---

### How It Works

**Method 1: Confidence-Based Variance**
- HIGH confidence (error <20%): ±10% variance
- MEDIUM confidence (error 20-50%): ±25% variance
- LOW confidence (error >50%): ±50% variance

**Method 2: Historical Error-Based Variance**
- Uses actual historical error for that route/model
- More accurate but requires history

---

### Usage

#### Add variance to existing forecasts:
```bash
python3 calculate_forecast_variance.py \
  --input data/forecasts/week_51_forecasts.csv \
  --output data/forecasts/week_51_forecasts_with_variance.csv \
  --method confidence
```

**Output columns added:**
- `forecast_low` - Lower bound (pessimistic)
- `forecast_high` - Upper bound (optimistic)
- `variance_pieces` - ±X pieces
- `variance_pct` - ±X%

---

### Example Output

```csv
route_key,forecast,confidence,forecast_low,forecast_high,variance_pieces,variance_pct
LAX-SFO-PKG-1,45.0,HIGH,40.5,49.5,4.5,10.0
NYC-BOS-DOC-5,12.0,HIGH,10.8,13.2,1.2,10.0
CHI-DET-PKG-3,89.0,MEDIUM,66.8,111.3,22.3,25.0
ATL-MIA-EXP-4,23.0,LOW,11.5,34.5,11.5,50.0
```

**For planning:**
- **Best case:** Use `forecast_high` (optimistic)
- **Worst case:** Use `forecast_low` (pessimistic)
- **Most likely:** Use `forecast` (point estimate)

---

## 2. MULTI-WEEK FORECASTING (6-Week Outlook)

### Why This Matters

Instead of forecasting just next week, forecast 6 weeks ahead:
- Week 51: 45 pieces ±10%
- Week 52: 47 pieces ±12%
- Week 53: 46 pieces ±14%
- Week 54: 48 pieces ±16%
- Week 55: 49 pieces ±18%
- Week 56: 50 pieces ±20%

**Use for:**
- Long-term capacity planning
- Staff scheduling 6 weeks out
- Resource procurement with lead time
- Scenario planning

---

### How It Works

**Key Features:**
1. Forecasts 1-6 weeks ahead (configurable)
2. Variance increases with horizon
   - Week 1: ±10% (most certain)
   - Week 6: ±20% (least certain)
3. Recursive forecasting (uses previous week's forecast)
4. Separate output from weekly forecasts

---

### Usage

#### Generate 6-week outlook:
```bash
python3 forecast_multi_week.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast routes_week_51.csv \
  --start-week 51 \
  --start-year 2025 \
  --num-weeks 6 \
  --output data/forecasts/multi_week_outlook_week51.csv
```

---

### Example Output

```csv
route_key,week_number,year,weeks_ahead,forecast,forecast_low,forecast_high,variance_pct
LAX-SFO-PKG-1,51,2025,1,45.0,40.5,49.5,10.0
LAX-SFO-PKG-1,52,2025,2,47.0,41.4,52.6,12.0
LAX-SFO-PKG-1,53,2025,3,46.0,39.6,52.4,14.0
LAX-SFO-PKG-1,54,2025,4,48.0,40.3,55.7,16.0
LAX-SFO-PKG-1,55,2025,5,49.0,40.2,57.8,18.0
LAX-SFO-PKG-1,56,2025,6,50.0,40.0,60.0,20.0
```

**For each route, you get 6 rows (one per week ahead)**

---

## COMBINED WORKFLOW

### Sunday Workflow with Variance & Multi-Week

#### Step 1: Generate 1-Week Forecast (Primary)
```bash
./sunday_weekly_update.sh 50 51 2025 8
```
**Output:** `data/forecasts/week_51_forecasts.csv`

#### Step 2: Add Variance to 1-Week Forecast
```bash
python3 calculate_forecast_variance.py \
  --input data/forecasts/week_51_forecasts.csv \
  --output data/forecasts/week_51_forecasts_with_variance.csv \
  --method confidence
```
**Output:** `week_51_forecasts_with_variance.csv` with confidence intervals

#### Step 3: Generate 6-Week Outlook (Optional)
```bash
python3 forecast_multi_week.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast routes_week_51.csv \
  --start-week 51 \
  --start-year 2025 \
  --num-weeks 6 \
  --output data/forecasts/multi_week_outlook_week51.csv
```
**Output:** `multi_week_outlook_week51.csv` with 6-week forecasts

---

## USE CASES

### Use Case 1: Weekly Operations
**Use:** 1-week forecast with variance
```
Week 51 forecast: 45 pieces [40-50 pieces]
Plan capacity: 50 pieces (use upper bound)
Staff: Based on 45 pieces (most likely)
Flex capacity: 10 pieces (variance)
```

### Use Case 2: Monthly Planning
**Use:** 4-week outlook
```
Week 51: 180 pieces ±10% = 162-198 pieces
Week 52: 190 pieces ±12% = 167-213 pieces
Week 53: 175 pieces ±14% = 151-200 pieces
Week 54: 185 pieces ±16% = 155-215 pieces

Total 4-week: 730 pieces [635-826 pieces]
Plan for: 826 pieces (worst case)
```

### Use Case 3: Quarterly Planning
**Use:** 6-week outlook with scenarios
```
Pessimistic (all forecast_low): 1,100 pieces
Most Likely (all forecast): 1,350 pieces
Optimistic (all forecast_high): 1,600 pieces

Budget for: 1,350 pieces
Reserve capacity for: 1,600 pieces
Minimum capacity: 1,100 pieces
```

---

## VARIANCE BY CONFIDENCE LEVEL

| Confidence | Error Range | Variance | Example Forecast | Range |
|------------|-------------|----------|------------------|-------|
| HIGH | <20% | ±10% | 100 pieces | 90-110 pieces |
| MEDIUM | 20-50% | ±25% | 100 pieces | 75-125 pieces |
| LOW | >50% | ±50% | 100 pieces | 50-150 pieces |
| NEW_ROUTE | Unknown | ±100% | 100 pieces | 0-200 pieces |

---

## VARIANCE BY FORECAST HORIZON

| Weeks Ahead | Variance Multiplier | Example (Base 10%) | Range for 100 pcs |
|-------------|--------------------|--------------------|-------------------|
| Week 1 | 1.0× | ±10% | 90-110 |
| Week 2 | 1.2× | ±12% | 88-112 |
| Week 3 | 1.4× | ±14% | 86-114 |
| Week 4 | 1.6× | ±16% | 84-116 |
| Week 5 | 1.8× | ±18% | 82-118 |
| Week 6 | 2.0× | ±20% | 80-120 |

**Why variance increases:**
- More time = more uncertainty
- Patterns can shift
- External factors have more time to impact
- Recursive forecasting compounds error

---

## INTEGRATION WITH SUNDAY WORKFLOW

### Updated Sunday Script (with variance)

Add to `sunday_weekly_update.sh` after Step 4:

```bash
# ============================================================
# STEP 5: Add Variance to Forecasts
# ============================================================
echo "STEP 5: Adding variance/confidence intervals..."
echo "-----------------------------------------------------------"

python3 calculate_forecast_variance.py \
  --input data/forecasts/week_${WEEK_THIS}_forecasts.csv \
  --output data/forecasts/week_${WEEK_THIS}_forecasts_with_variance.csv \
  --method confidence

echo "✅ Variance added to forecasts"
echo ""

# ============================================================
# STEP 6: Generate 6-Week Outlook (Optional)
# ============================================================
echo "STEP 6: Generating 6-week outlook..."
echo "-----------------------------------------------------------"

python3 forecast_multi_week.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
  --routes-to-forecast routes_week_${WEEK_THIS}.csv \
  --start-week $WEEK_THIS \
  --start-year $YEAR \
  --num-weeks 6 \
  --output data/forecasts/multi_week_outlook_week${WEEK_THIS}.csv

echo "✅ 6-week outlook generated"
echo ""
```

---

## SAMPLE OUTPUTS

### 1-Week Forecast with Variance
```
Route: LAX-SFO-Package-Monday
Forecast: 45 pieces
Range: 40 - 50 pieces (±5 pieces, ±11%)
Confidence: HIGH
Model Used: 04_Recent_8W

→ Plan for 50 pieces capacity (upper bound)
→ Expect 45 pieces (most likely)
→ Minimum 40 pieces (lower bound)
```

### 6-Week Outlook
```
Route: LAX-SFO-Package-Monday

Week 51 (1 ahead): 45 pcs [40-50] ±10%  ← Most certain
Week 52 (2 ahead): 47 pcs [41-53] ±12%
Week 53 (3 ahead): 46 pcs [40-53] ±14%
Week 54 (4 ahead): 48 pcs [40-56] ±16%
Week 55 (5 ahead): 49 pcs [40-58] ±18%
Week 56 (6 ahead): 50 pcs [40-60] ±20%  ← Least certain

Total 6-week: 285 pcs [241-330]

→ Plan capacity: 330 pieces (worst case across 6 weeks)
→ Expected volume: 285 pieces
→ Minimum volume: 241 pieces
```

---

## BEST PRACTICES

### ✅ DO:
- Use 1-week forecast for immediate operations (most accurate)
- Use variance for capacity planning and buffers
- Use 6-week outlook for long-term planning
- Update 6-week outlook every week (rolling forecast)
- Plan capacity to upper bound, staff to most likely

### ❌ DON'T:
- Rely on Week 6 forecast for critical decisions (too uncertain)
- Ignore variance (point estimates are incomplete)
- Use same buffer for all routes (HIGH vs LOW confidence matters)
- Forget to update multi-week forecasts weekly

---

## QUICK REFERENCE

### Add variance to forecasts:
```bash
python3 calculate_forecast_variance.py \
  --input week_51_forecasts.csv \
  --output week_51_with_variance.csv \
  --method confidence
```

### Generate 6-week outlook:
```bash
python3 forecast_multi_week.py \
  --routing-table routing_table_current.csv \
  --historical-data historical_data.csv \
  --routes-to-forecast routes.csv \
  --start-week 51 \
  --start-year 2025 \
  --num-weeks 6 \
  --output multi_week_outlook.csv
```

### Check variance summary:
```bash
python3 calculate_forecast_variance.py --input ... | grep "Variance Summary"
```

---

## ANSWERS TO YOUR QUESTIONS

**Q: "Like HIGH confidence ±1 or LOW confidence ±30?"**

✅ **Yes! Exactly!** The variance calculation does this:
- HIGH confidence: ±10% (e.g., 45 pieces → ±4.5 pieces)
- LOW confidence: ±50% (e.g., 45 pieces → ±22.5 pieces)

**Q: "How would this change if we tried to make a 6-week outlook?"**

✅ **Yes! Separate script:** `forecast_multi_week.py`
- Variance increases with each week out
- Week 1: ±10%, Week 6: ±20%
- Gives you 6 rows per route (one per week)

**Q: "Can we do that in the same notebook or should we keep it separate?"**

✅ **Recommended: Keep separate**
- 1-week forecast: Primary, most accurate, use for weekly operations
- 6-week outlook: Secondary, less accurate, use for planning
- Different outputs prevent confusion
- Can run both every Sunday if needed

---

**Both features are ready to use! Add them to your Sunday workflow for complete forecasting.** 🎯
