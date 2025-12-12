# Model 2: Baseline + YoY Trend Forecast

## 📊 Overview

**Baseline with growth/decline adjustment** - Captures Year-over-Year trends.

- **Accuracy**: 92-93% baseline + trend adjustment
- **Complexity**: ⭐⭐ Medium (adds one calculation)
- **Best for**: Regular weeks with growth/decline patterns

---

## 🎯 Methodology

### Core Concept
Take Model 1 (baseline) and multiply by Year-over-Year growth rate.

### Two-Step Process

#### Step 1: Get Baseline
- MAX: Use 2022 Week N
- EXP: Use 2024 Week N
- *Same as Model 1*

#### Step 2: Calculate YoY Trend
- Compare recent 8 weeks to same 8 weeks last year
- Calculate growth multiplier
- **Trend = Recent_8W_Avg / LastYear_8W_Avg**

### Formula

```
For each product type:

  1. baseline = Historical baseline (2022 MAX, 2024 EXP)

  2. trend = Recent_8_Weeks_Avg / LastYear_Same_8_Weeks_Avg

  3. Forecast = baseline × trend

Example:
  baseline = 1,000 pieces
  trend = 1.05 (5% growth)
  forecast = 1,000 × 1.05 = 1,050 pieces
```

---

## 🚀 How to Run

### Basic Usage

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
source venv/bin/activate
python src/forecast_trend.py --week 51 --year 2025
```

### With Custom Output

```bash
python src/forecast_trend.py --week 51 --year 2025 --output forecasts/trend_w51.csv
```

### Help

```bash
python src/forecast_trend.py --help
```

---

## 📥 Inputs

### Required
- `--week`: Target week number (1-53)
- `--year`: Target year (e.g., 2025)

### Optional
- `--output`: Output CSV file path
- `--table`: Databricks table name

### Data Requirements
- ✅ 2022 data for MAX baseline
- ✅ 2024 data for EXP baseline
- ✅ Recent 8 weeks of current year data
- ✅ Same 8 weeks from previous year

---

## 📤 Outputs

### CSV File

**Filename format**: `trend_week_{week}_{year}_{timestamp}.csv`

Example: `trend_week_51_2025_20251212_143022.csv`

### Columns

| Column | Type | Description |
|--------|------|-------------|
| ODC | string | Origin Distribution Center |
| DDC | string | Destination Distribution Center |
| dayofweek | int | Day of week (0=Monday, 6=Sunday) |
| baseline | float | Historical baseline volume |
| trend | float | YoY growth multiplier (e.g., 1.05 = +5%) |
| **forecast** | float | **Final forecast (baseline × trend)** ⭐ |
| ProductType | string | MAX or EXP |
| baseline_year | int | 2022 (MAX) or 2024 (EXP) |
| method | string | "Baseline_Plus_Trend" |
| week | int | Target week |
| year | int | Target year |

---

## 📊 Example Output

### Console

```
======================================================================
METHOD 2: BASELINE + YoY TREND FORECAST
Baseline (92-93%) + YoY Growth Adjustment
======================================================================

✅ Connected to Azure Databricks
📊 Loading historical data...
✅ Loaded 358,820 records

======================================================================
METHOD 2: BASELINE + YoY TREND FORECAST
Week 51, 2025
======================================================================

📊 MAX Product:
   Step 1: Get 2022 Week N baseline
      ✅ Baseline: 12,345 pieces
   Step 2: Calculate YoY trend
      📈 Trend: 1.050 (↑ 5.0%)
   ✅ Final: 12,962 pieces

📊 EXP Product:
   Step 1: Get 2024 Week N baseline
      ✅ Baseline: 4,789 pieces
   Step 2: Calculate YoY trend
      📈 Trend: 0.980 (↓ 2.0%)
   ✅ Final: 4,693 pieces

📊 Forecast Summary:
ProductType  baseline  forecast  change_%
MAX          12345.0   12962.0       5.0
EXP           4789.0    4693.0      -2.0

✅ Total Forecast: 17,655 pieces
   (vs 17,134 baseline = +3.0% change)

💾 Saved to: trend_week_51_2025_20251212_143022.csv
```

### CSV Sample

```csv
ODC,DDC,dayofweek,baseline,trend,forecast,ProductType,baseline_year,method,week,year
LAX,SFO,0,125.5,1.050,131.8,MAX,2022,Baseline_Plus_Trend,51,2025
LAX,SFO,1,450.2,1.050,472.7,MAX,2022,Baseline_Plus_Trend,51,2025
LAX,PHX,0,89.3,0.980,87.5,EXP,2024,Baseline_Plus_Trend,51,2025
```

---

## ✅ Strengths

### 1. Captures Growth/Decline
- Reflects recent business trends
- Adapts to market changes
- More accurate when trends exist

**Example**: If business grew 5% YoY, forecast reflects that

### 2. Still Simple
- Only adds one calculation
- Easy to understand and explain
- Transparent methodology

### 3. Improved Accuracy
- Better than baseline when trends exist
- Small overhead for meaningful gain
- Product-specific trends

### 4. Flexibility
- Trend updates automatically
- Adapts to recent data
- No manual intervention needed

---

## ⚠️ Limitations

### 1. No Seasonal Adjustment
- Still misses peak season patterns
- Treats Week 50 (peak) same as Week 20 (regular)
- Use Model 3 for peak weeks

**Example**: Week 50 should be 1.27x higher, this model misses that

### 2. Assumes Linear Trends
- Growth/decline assumed constant
- Can't capture acceleration
- Simple average-based calculation

### 3. Sensitive to Data Quality
- Outliers affect trend calculation
- Requires clean 8-week windows
- Missing data = default trend of 1.0

### 4. Recent Data Dependency
- Needs current year data
- If forecasting early in year, trend may be unstable
- Last year data required for comparison

---

## 🎯 When to Use

### ✅ Use Baseline + Trend When:

1. **Regular (Non-Peak) Weeks**
   - Weeks 1-47, 53
   - Normal business patterns
   - Seasonal adjustment not needed

2. **Clear Growth/Decline**
   - Business expanding
   - Market contracting
   - Recent trend matters

3. **Want More Accuracy Than Baseline**
   - Baseline alone underestimates/overestimates
   - Small improvement justified
   - Still want simplicity

4. **Production Forecasting**
   - Regular weekly forecasts
   - Standard operations
   - Balanced accuracy/complexity

### ❌ Don't Use When:

1. **Peak Season (Weeks 48-52)**
   - Use Model 3 (includes seasonal)
   - Trend alone misses holiday surge

2. **Insufficient Recent Data**
   - Less than 8 weeks available
   - Data quality issues
   - Use Model 1 instead

3. **Highly Volatile Business**
   - Trends change rapidly
   - Not stable enough for 8-week average
   - Consider shorter windows (custom)

---

## 📈 Accuracy Details

### Expected Performance

| Scenario | Accuracy | Notes |
|----------|----------|-------|
| Steady state (trend = 1.0) | 92-93% | Same as Model 1 |
| Growth (trend = 1.05) | 94-96% | Better than baseline |
| Decline (trend = 0.95) | 93-95% | Better than baseline |
| Peak season | 85-88% | Use Model 3 instead |

### Trend Multiplier Ranges

**Typical ranges observed**:
- **MAX Product**: 0.95 - 1.10 (±5-10%)
- **EXP Product**: 0.90 - 1.15 (±10-15%, more volatile)

**Extreme values to investigate**:
- Trend < 0.80 (20% decline) - Check for data issues
- Trend > 1.20 (20% growth) - Verify if real or anomaly

---

## 🔍 Understanding Trend Values

### Interpreting Trend Multipliers

#### Trend = 1.05 (5% growth)
```
Interpretation: Business grew 5% YoY
Forecast: 5% higher than baseline
Example: 1,000 → 1,050 pieces
```

#### Trend = 0.95 (5% decline)
```
Interpretation: Business declined 5% YoY
Forecast: 5% lower than baseline
Example: 1,000 → 950 pieces
```

#### Trend = 1.00 (no change)
```
Interpretation: Stable business
Forecast: Same as baseline
Example: 1,000 → 1,000 pieces
```

### Product-Specific Trends

Often see different trends by product:

```
MAX Trend: 1.05 (↑ 5.0%)
EXP Trend: 0.98 (↓ 2.0%)

Interpretation:
- MAX growing (mature product expanding)
- EXP slightly declining (competitive pressure?)
```

This is **normal** - products behave differently.

---

## 🧮 Trend Calculation Details

### Algorithm

```python
def calculate_yoy_trend(df, target_week, target_year, product_type):
    # Define 8-week lookback window
    recent_weeks = range(target_week - 8, target_week)
    # e.g., for Week 51: [43, 44, 45, 46, 47, 48, 49, 50]

    # Get recent data (current year)
    recent_data = df[
        (df['year'] == target_year) &  # 2025
        (df['week'].isin(recent_weeks)) &
        (df['ProductType'] == product_type)
    ]
    recent_avg = recent_data['pieces'].mean()

    # Get last year same weeks
    lastyear_data = df[
        (df['year'] == target_year - 1) &  # 2024
        (df['week'].isin(recent_weeks)) &
        (df['ProductType'] == product_type)
    ]
    lastyear_avg = lastyear_data['pieces'].mean()

    # Calculate trend
    trend = recent_avg / lastyear_avg if lastyear_avg > 0 else 1.0

    return trend
```

### Why 8 Weeks?

- **Stable**: Enough data to smooth out noise
- **Recent**: Captures current trends
- **Practical**: Usually available
- **Tested**: Best performance in 100+ experiments

### Edge Cases

**Missing data**:
- If < 8 weeks available: Use what's available
- If no data: Default to trend = 1.0 (no adjustment)

**Zero division**:
- If last year = 0: Default to trend = 1.0

---

## 🧪 Testing & Validation

### 1. Run Test Forecast

```bash
# Forecast Week 50, 2024 (known actuals)
python src/forecast_trend.py --week 50 --year 2024
```

### 2. Check Trend Values

```python
import pandas as pd

df = pd.read_csv('trend_week_50_2024_*.csv')

# Check trends
trends = df.groupby('ProductType')['trend'].first()
print(trends)

# Should see reasonable values (0.9 - 1.1)
```

### 3. Compare with Baseline

```bash
# Run both models
python src/forecast_baseline.py --week 50 --year 2024
python src/forecast_trend.py --week 50 --year 2024

# Compare totals
```

---

## 🔧 Troubleshooting

### Trend = 1.0 for Both Products

**Possible causes**:
1. Insufficient recent data
2. Missing last year data
3. Data quality issue

**Debug**:
```sql
-- Check recent 8 weeks (e.g., Weeks 43-50 for target Week 51)
SELECT
    YEAR(DATE_SHIP) as year,
    WEEK(DATE_SHIP) as week,
    ProductType,
    SUM(PIECES) as total
FROM decus_domesticops_prod.dbo.tmp_hassett_report
WHERE WEEK(DATE_SHIP) BETWEEN 43 AND 50
    AND YEAR(DATE_SHIP) IN (2024, 2025)
GROUP BY 1,2,3
ORDER BY 1,2,3
```

### Extreme Trend Values (>1.5 or <0.5)

**Likely issues**:
- Data quality problem
- Major business change
- Seasonal pattern in lookback window

**Actions**:
1. Investigate data
2. Check for outliers
3. Consider shorter/longer window
4. Verify business context

### Forecast vs Baseline Huge Difference

**If >20% difference**:
- Review trend calculation
- Check recent data
- Validate with business team

---

## 💡 Tips

### 1. Monitor Trend Values

```python
# Track trends over time
trends_log = []
for week in range(45, 53):
    # Run forecast, extract trend
    # Log to trends_log

# Plot trends over time
# Spot anomalies
```

### 2. Validate Against Actuals

```python
# After actual data arrives
actual_trend = actuals_2025 / actuals_2024
forecast_trend = df['trend'].iloc[0]

print(f"Actual YoY: {actual_trend:.3f}")
print(f"Forecast YoY: {forecast_trend:.3f}")
print(f"Difference: {abs(actual_trend - forecast_trend):.3f}")
```

### 3. Adjust Window Size

If 8 weeks doesn't work well:

```python
# Modify script to use 4 weeks
recent_weeks = range(target_week - 4, target_week)

# Or 12 weeks
recent_weeks = range(target_week - 12, target_week)
```

### 4. Combine with Model 1

```bash
# Run both
python src/forecast_baseline.py --week 51 --year 2025
python src/forecast_trend.py --week 51 --year 2025

# Average the forecasts for ensemble
```

---

## 📚 Advanced Usage

### Custom Trend Calculation

Edit `src/forecast_trend.py`:

```python
# Use weighted average instead of simple mean
weights = [1, 1, 1, 1, 2, 2, 3, 3]  # More weight on recent weeks
recent_avg = np.average(recent_data_by_week, weights=weights)
```

### Product-Specific Windows

```python
# MAX: Use 8 weeks (stable)
max_weeks = 8

# EXP: Use 4 weeks (more volatile)
exp_weeks = 4
```

---

## 📞 Next Steps

1. **Run Model 2 forecast**
   ```bash
   python src/forecast_trend.py --week 51 --year 2025
   ```

2. **Compare with Model 1**
   ```bash
   # Check difference
   # If similar: trends are stable
   # If different: trends matter
   ```

3. **Try Model 3 for peak weeks**
   ```bash
   python src/forecast_integrated.py --week 51 --year 2025
   ```

4. **Run all 3 models**
   ```bash
   python run_all_models.py --week 51 --year 2025
   ```

---

## 📖 Related Documentation

- **Model 1 (Baseline)**: `MODEL_1_BASELINE.md`
- **Model 3 (Integrated)**: `MODEL_3_INTEGRATED.md`
- **Model Comparison**: `MODELS_GUIDE.md`
- **Methodology**: `docs/META_ANALYSIS_100_EXPERIMENTS.md`

---

**Summary**: Model 2 adds YoY trend adjustment to the baseline, capturing growth or decline. Best for regular weeks when recent trends matter. For peak season, use Model 3.

Expected accuracy: **92-93% + trend benefit** 📈
