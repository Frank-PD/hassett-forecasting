# Model 1: Baseline Only Forecast

## 📊 Overview

**Simplest forecasting approach** - Uses historical baseline data with **NO adjustments**.

- **Accuracy**: 92-93% overall (MAX: 93.46%, EXP: 86.37%)
- **Complexity**: ⭐ Low (easiest to understand)
- **Best for**: Stable business, quick estimates, baseline comparisons

---

## 🎯 Methodology

### Core Concept
Use the optimal historical week as the forecast, with no adjustments for trends or seasonality.

### Product-Specific Baselines

#### MAX Product:
- **Source**: 2022 Week N
- **Why**: 93.46% accuracy in validation
- **Logic**: 2022 MAX patterns closely match current behavior

#### EXP Product:
- **Source**: 2024 Week N
- **Why**: 86.37% accuracy in validation
- **Logic**: EXP product is newer, 2024 data more relevant

### Formula

```
For each ODC-DDC-DayOfWeek combination:

  Forecast = Historical_Baseline

  Where:
    Historical_Baseline = AVG(pieces) from optimal year
```

**That's it!** No multipliers, no adjustments, no complexity.

---

## 🚀 How to Run

### Basic Usage

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
source venv/bin/activate
python src/forecast_baseline.py --week 51 --year 2025
```

### With Custom Output

```bash
python src/forecast_baseline.py --week 51 --year 2025 --output my_forecast.csv
```

### Help

```bash
python src/forecast_baseline.py --help
```

---

## 📥 Inputs

### Required
- `--week`: Target week number (1-53)
- `--year`: Target year (e.g., 2025)

### Optional
- `--output`: Output CSV file path (default: auto-generated)
- `--table`: Databricks table name

### Data Requirements
- ✅ 2022 data for MAX product
- ✅ 2024 data for EXP product
- ✅ Complete ODC, DDC, DATE_SHIP, PIECES columns

---

## 📤 Outputs

### CSV File

**Filename format**: `baseline_week_{week}_{year}_{timestamp}.csv`

Example: `baseline_week_51_2025_20251212_143022.csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ODC | string | Origin Distribution Center |
| DDC | string | Destination Distribution Center |
| dayofweek | int | Day of week (0=Monday, 6=Sunday) |
| **forecast** | float | **Final forecasted pieces** ⭐ |
| ProductType | string | MAX or EXP |
| baseline_year | int | Source year (2022 for MAX, 2024 for EXP) |
| method | string | "Baseline_Only" |
| week | int | Target week number |
| year | int | Target year |

---

## 📊 Example Output

### Console

```
======================================================================
METHOD 1: SIMPLE BASELINE FORECAST
Expected Accuracy: 92-93% (MAX: 93.46%, EXP: 86.37%)
======================================================================

✅ Connected to Azure Databricks
📊 Loading historical data...
✅ Loaded 358,820 records
📅 Date range: 2022-01-01 to 2024-12-31

======================================================================
METHOD 1: SIMPLE BASELINE FORECAST
Week 51, 2025
======================================================================

📊 MAX Product: Using 2022 Week N baseline
   ✅ 1,234 routes, 12,345 pieces

📊 EXP Product: Using 2024 Week N baseline
   ✅ 567 routes, 4,789 pieces

📊 Forecast Summary:
   MAX:       12,345 pieces
   EXP:        4,789 pieces

✅ Total Forecast: 17,134 pieces

💾 Saved to: baseline_week_51_2025_20251212_143022.csv

======================================================================
✅ FORECAST COMPLETE!
======================================================================
```

### CSV Sample

```csv
ODC,DDC,dayofweek,forecast,ProductType,baseline_year,method,week,year
LAX,SFO,0,125.5,MAX,2022,Baseline_Only,51,2025
LAX,SFO,1,450.2,MAX,2022,Baseline_Only,51,2025
LAX,PHX,0,89.3,EXP,2024,Baseline_Only,51,2025
```

---

## ✅ Strengths

### 1. Simplicity
- Easy to understand
- Easy to explain to stakeholders
- No complex parameters

### 2. Stability
- Consistent results
- No volatility from adjustments
- Reliable baseline for comparisons

### 3. Accuracy
- **92-93% overall accuracy**
- Proven methodology from 100+ experiments
- Strong performance without complexity

### 4. Speed
- Fast execution
- Minimal data requirements
- No complex calculations

---

## ⚠️ Limitations

### 1. Misses Trends
- Doesn't capture growth
- Doesn't account for decline
- Assumes business is steady-state

**Example**: If business grew 10% YoY, forecast will underestimate by ~10%

### 2. Ignores Seasonality
- No peak season adjustment
- No holiday patterns
- Flat multiplier of 1.0x

**Example**: Week 50 (peak season) gets same treatment as Week 20 (regular)

### 3. Fixed Historical Period
- MAX locked to 2022
- EXP locked to 2024
- Can't adapt to recent changes

---

## 🎯 When to Use

### ✅ Use Baseline Only When:

1. **Quick Estimate Needed**
   - Fast turnaround required
   - Rough ballpark sufficient
   - Complexity not justified

2. **Stable Business**
   - No major growth/decline
   - Consistent patterns
   - Regular (non-peak) weeks

3. **Comparison Baseline**
   - Testing other models
   - Need simple reference
   - Benchmarking purposes

4. **First-Time Forecast**
   - Learning the system
   - Understanding the data
   - Building confidence

### ❌ Don't Use When:

1. **Peak Season (Weeks 48-52)**
   - Needs seasonal adjustment
   - Use Model 3 instead

2. **Strong Growth/Decline**
   - Recent trends important
   - Use Model 2 or 3 instead

3. **High Accuracy Critical**
   - Use Model 3 (full integrated)
   - Adds only ~1-2% but could matter

---

## 📈 Accuracy Details

### Validation Results

From 100+ experiments validating against Week 50, 2024:

| Metric | MAX | EXP | Overall |
|--------|-----|-----|---------|
| Accuracy | 93.46% | 86.37% | 92-93% |
| MAE (pieces) | ~7.5 | ~15.2 | ~9.8 |
| R² | 0.0173 | negative | 0.0173 |

**Accuracy = 1 - abs(forecast - actual) / actual**

### By Tier

| ODC Tier | Accuracy | Notes |
|----------|----------|-------|
| Large (LAX, EWR, IAD, SLC) | 85-95% | Variable (LAX can be tricky) |
| Medium (ATL, DFW, PHX, etc.) | 92-96% | Most consistent |
| Small (MCI, CAK, MCO, etc.) | 88-94% | Good overall |

---

## 🔍 Understanding the Output

### Interpreting Forecast Values

**High values (>1000 pieces/day)**:
- Major routes (LAX, EWR, IAD)
- Verify they make sense
- Check for outliers

**Low values (<10 pieces/day)**:
- Minor routes or specific days
- Normal for smaller DDCs
- Monday often has lower volume

### Day-of-Week Patterns

Typical distribution:
- **Monday**: ~8-10% (lighter, holiday pattern)
- **Tuesday**: ~30% (ramp-up)
- **Wednesday**: ~30% (peak mid-week)
- **Thursday**: ~30% (sustained)
- **Friday-Sunday**: ~0-2% (minimal)

---

## 🧪 Testing & Validation

### 1. Run Test Forecast

```bash
python src/forecast_baseline.py --week 50 --year 2024
```

### 2. Compare with Actuals

```python
import pandas as pd

# Load forecast
forecast = pd.read_csv('baseline_week_50_2024_*.csv')

# Load actuals from Databricks
# ... (query actual data)

# Compare
comparison = forecast.merge(actuals, on=['ODC', 'DDC', 'ProductType', 'dayofweek'])
comparison['accuracy'] = 1 - abs(comparison['forecast'] - comparison['actual']) / comparison['actual']

print(f"Overall Accuracy: {comparison['accuracy'].mean():.2%}")
```

### 3. Expected Result

Should see ~92-93% accuracy overall.

---

## 🔧 Troubleshooting

### "No 2022 MAX data found"

**Cause**: Missing 2022 data in Databricks table

**Fix**:
```bash
# Check data availability
python test_forecast.py

# Or query Databricks directly
# SELECT COUNT(*) FROM ... WHERE YEAR(DATE_SHIP) = 2022 AND ProductType = 'MAX'
```

### "No 2024 EXP data found"

**Cause**: Missing 2024 EXP data

**Fix**: Same as above, check data availability

### Forecast seems too low/high

**Possible causes**:
1. Data quality issues (check for outliers)
2. Missing data for that week
3. Unusual historical patterns

**Debug**:
```sql
-- Check historical baseline
SELECT
    YEAR(DATE_SHIP) as year,
    WEEK(DATE_SHIP) as week,
    ProductType,
    SUM(PIECES) as total
FROM decus_domesticops_prod.dbo.tmp_hassett_report
WHERE WEEK(DATE_SHIP) = 51
GROUP BY 1,2,3
```

---

## 📚 Technical Details

### Algorithm

```python
def generate_baseline_forecast(df, target_week, target_year):
    # MAX: Get 2022 Week N data
    max_baseline = df[
        (df['year'] == 2022) &
        (df['week'] == target_week) &
        (df['ProductType'] == 'MAX')
    ]

    # Aggregate by route-day
    max_forecast = max_baseline.groupby(
        ['ODC', 'DDC', 'dayofweek']
    )['pieces'].mean()

    # EXP: Get 2024 Week N data
    exp_baseline = df[
        (df['year'] == 2024) &
        (df['week'] == target_week) &
        (df['ProductType'] == 'EXP')
    ]

    exp_forecast = exp_baseline.groupby(
        ['ODC', 'DDC', 'dayofweek']
    )['pieces'].mean()

    # Combine
    forecast = pd.concat([max_forecast, exp_forecast])

    return forecast
```

### Data Aggregation

- **Grouping**: ODC, DDC, dayofweek, ProductType
- **Metric**: Mean (average pieces)
- **Why mean**: Handles multiple dates in same week/year/dow

---

## 💡 Tips

1. **Run for Past Weeks First**
   - Test on Week 50 2024 (known actuals)
   - Validate accuracy before forecasting future

2. **Compare with Actuals**
   - Track accuracy over time
   - Identify problem ODCs

3. **Use as Baseline**
   - Compare Model 2 & 3 against this
   - Understand impact of adjustments

4. **Archive Outputs**
   - Keep historical forecasts
   - Track performance trends

---

## 📞 Next Steps

### After Running Baseline Forecast:

1. **Review output CSV**
   - Check totals make sense
   - Look for outliers

2. **Try Model 2 (Baseline + Trend)**
   ```bash
   python src/forecast_trend.py --week 51 --year 2025
   ```

3. **Compare all models**
   ```bash
   python run_all_models.py --week 51 --year 2025
   ```

4. **Read methodology**
   - `docs/META_ANALYSIS_100_EXPERIMENTS.md`

---

## 📖 Related Documentation

- **Model 2 (Trend)**: `MODEL_2_TREND.md`
- **Model 3 (Integrated)**: `MODEL_3_INTEGRATED.md`
- **Model Comparison**: `MODELS_GUIDE.md`
- **Quick Start**: `QUICKSTART.md`

---

**Summary**: Model 1 is the simplest, most stable forecasting approach. Use it for quick estimates or as a baseline for comparison. For peak season or when trends matter, consider Model 2 or 3.

Expected accuracy: **92-93%** 🎯
