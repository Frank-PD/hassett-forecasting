# Quick Start Guide

## 🚀 Run Forecast in 3 Steps

### Option 1: Using the Script (Easiest)

```bash
# 1. Navigate to project
cd /Users/frankgiles/Downloads/hassett-forecasting

# 2. Activate environment
source venv/bin/activate

# 3. Run forecast
python src/forecast.py --week 51 --year 2025
```

**Example output:**
```
✅ Connected to Azure Databricks
📊 Loading historical data from Databricks...
✅ Loaded 358,820 records
📅 Date range: 2022-01-01 to 2024-12-31

🎄 Seasonal Multiplier: 1.25x
   ⚠️  Peak season week detected!

📊 Step 1: Calculate Baselines
   MAX (2022 Week 51): 12,345 pieces
   EXP (2024 Week 51): 4,789 pieces

📈 Step 2: Calculate YoY Trends
   MAX Trend: 1.050 (↑ 5.0%)
   EXP Trend: 0.980 (↓ 2.0%)

✅ Total Forecast: 18,234 pieces

💾 Forecast saved to: forecast_week_51_2025_20251212_140530.csv
```

---

## 📋 Command Options

### Basic Usage
```bash
python src/forecast.py --week 51 --year 2025
```

### Save to Specific File
```bash
python src/forecast.py --week 51 --year 2025 --output my_forecast.csv
```

### Use Different Table
```bash
python src/forecast.py --week 51 --year 2025 --table my_schema.hassett_data
```

### Skip Detailed Summary
```bash
python src/forecast.py --week 51 --year 2025 --no-summary
```

---

## 🔧 Using the Shell Script (Even Easier)

```bash
# Make it executable (first time only)
chmod +x run_forecast.sh

# Run with defaults (Week 51, 2025)
./run_forecast.sh

# Run with custom week and year
./run_forecast.sh 50 2025

# Run for Week 1 of 2026
./run_forecast.sh 1 2026
```

---

## 📊 Output Files

The forecast generates a CSV file with these columns:

| Column | Description |
|--------|-------------|
| `ODC` | Origin Distribution Center |
| `DDC` | Destination Distribution Center |
| `dayofweek` | 0=Monday, 6=Sunday |
| `baseline` | Historical baseline volume |
| `ProductType` | MAX or EXP |
| `baseline_year` | Year used for baseline (2022 for MAX, 2024 for EXP) |
| `trend` | YoY trend multiplier |
| `seasonal` | Seasonal adjustment multiplier |
| `forecast` | **Final forecast** (pieces) |
| `week` | Target week number |
| `year` | Target year |

---

## 🎯 Example Workflows

### 1. Generate Forecast for Next Week
```bash
python src/forecast.py --week 51 --year 2025 --output forecasts/week_51.csv
```

### 2. Batch Generate Multiple Weeks
```bash
for week in {48..52}; do
    python src/forecast.py --week $week --year 2025 --output forecasts/week_${week}.csv
done
```

### 3. Compare with Actuals
```python
import pandas as pd

# Load forecast
forecast = pd.read_csv('forecast_week_51_2025.csv')

# Load actuals from Databricks
actuals = pd.read_sql("SELECT * FROM actuals WHERE week=51 AND year=2025", conn)

# Compare
comparison = forecast.merge(actuals, on=['ODC', 'DDC', 'ProductType'])
comparison['accuracy'] = 1 - abs(comparison['forecast'] - comparison['actual']) / comparison['actual']
print(f"Overall Accuracy: {comparison['accuracy'].mean():.2%}")
```

---

## 📓 Using Jupyter Notebooks

If you prefer interactive development:

```bash
# 1. Start Jupyter
jupyter notebook

# 2. Open notebooks/01_quick_forecast.ipynb

# 3. Update Cell 2 to use Databricks:
from databricks import sql
conn = sql.connect(
    server_hostname="adb-434028626745069.9.azuredatabricks.net",
    http_path="/sql/1.0/warehouses/23a9897d305fb7e2",
    auth_type="databricks-oauth"
)

# 4. Run all cells
```

---

## 🔍 Troubleshooting

### "No module named 'databricks'"
```bash
pip install databricks-sql-connector
```

### "Authentication failed"
```bash
# Make sure you're logged into Databricks CLI
databricks auth login --host https://adb-434028626745069.9.azuredatabricks.net

# Or set environment variables
export DATABRICKS_TOKEN="your_token_here"
```

### "Table not found"
```bash
# Specify the full table path
python src/forecast.py --week 51 --year 2025 --table catalog.schema.hassett_report
```

### "No baseline data found"
This means there's no historical data for that week. Check:
- Is the week number valid? (1-53)
- Do you have 2022 data for MAX?
- Do you have 2024 data for EXP?

---

## 📈 Expected Accuracy

Based on 100+ experiments:

| Product | Accuracy | Method |
|---------|----------|--------|
| MAX | 93-94% | 2022 Week N baseline |
| EXP | 86-88% | 2024 Week N baseline |
| **Overall** | **92-93%** | Integrated system |

Accuracy = `1 - abs(forecast - actual) / actual`

---

## 🎄 Peak Season Weeks

The system automatically applies seasonal multipliers:

| Week | Period | Multiplier |
|------|--------|------------|
| 48 | Thanksgiving | 1.20x |
| 49 | Pre-peak | 1.25x |
| 50 | Peak | 1.27x |
| 51 | Peak | 1.25x |
| 52 | Christmas | 1.15x |

---

## 💡 Tips

1. **Run forecasts weekly** - Update with latest YoY trends
2. **Review outliers** - Check ODCs with unusual patterns
3. **Validate results** - Compare with recent actuals
4. **Archive outputs** - Keep CSV files for audit trail
5. **Monitor accuracy** - Track performance over time

---

## 📚 Next Steps

- [ ] Review `docs/META_ANALYSIS_100_EXPERIMENTS.md` for methodology details
- [ ] Set up automated weekly forecasting (cron job)
- [ ] Create dashboard to visualize results
- [ ] Implement accuracy monitoring system
- [ ] Build alerting for anomalies

---

**Need Help?**
- Check `README.md` for project overview
- Review `NOTEBOOK_SETUP.md` for Jupyter setup
- See `docs/FORECASTING_PACKAGES_USED.md` for technical details

Happy forecasting! 📊🎯
