# 🚀 Ready to Run - Hassett Forecasting System

## ✅ What's Ready

Your forecasting system is **fully configured and ready to run**!

### 📦 What You Have

1. **Production Forecasting Script** (`src/forecast.py`)
   - Connects to Databricks
   - Implements 92-93% accuracy methodology
   - Generates forecasts on demand
   - Outputs CSV files

2. **Databricks Connection** (✅ Tested & Working)
   - Server: `adb-434028626745069.9.azuredatabricks.net`
   - Warehouse: `/sql/1.0/warehouses/23a9897d305fb7e2`
   - Table: `decus_domesticops_prod.dbo.tmp_hassett_report`

3. **Interactive Notebooks** (2 files)
   - `00_setup_and_test.ipynb` - Environment test ✅
   - `01_quick_forecast.ipynb` - Forecasting demo

4. **Documentation**
   - `QUICKSTART.md` - How to run forecasts
   - `README.md` - Project overview
   - `docs/META_ANALYSIS_100_EXPERIMENTS.md` - Full methodology

---

## 🎯 Run Your First Forecast (3 Ways)

### Option 1: Using Python Script (Recommended)

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
source venv/bin/activate
python src/forecast.py --week 51 --year 2025
```

**Output:** CSV file with day-level forecasts for all ODC-DDC routes

---

### Option 2: Using Shell Script (Easiest)

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
./run_forecast.sh 51 2025
```

---

### Option 3: Using Jupyter Notebook (Interactive)

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
jupyter notebook
# Open: notebooks/01_quick_forecast.ipynb
# Change TARGET_WEEK = 51, TARGET_YEAR = 2025
# Click "Run All"
```

---

## 📊 What the Forecast Does

### Input
- **Target Week**: e.g., Week 51
- **Target Year**: e.g., 2025

### Process (Automatic)
1. ✅ Connect to Databricks
2. ✅ Load historical data from `decus_domesticops_prod.dbo.tmp_hassett_report`
3. ✅ Calculate baseline (2022 for MAX, 2024 for EXP)
4. ✅ Apply YoY trend adjustment
5. ✅ Apply seasonal multiplier (1.25x for Week 51)
6. ✅ Generate day-level forecasts for each ODC-DDC route

### Output
CSV file with columns:
- `ODC`, `DDC`, `ProductType` (MAX/EXP)
- `dayofweek` (0=Mon, 6=Sun)
- `baseline` - Historical baseline volume
- `trend` - YoY growth multiplier
- `seasonal` - Seasonal adjustment
- **`forecast`** ⭐ - Final forecasted pieces
- `week`, `year`

---

## 🧪 Test Before First Run

**Recommended:** Run the test script first to verify everything works:

```bash
cd /Users/frankgiles/Downloads/hassett-forecasting
source venv/bin/activate
python test_forecast.py
```

This checks:
- ✅ Databricks connection
- ✅ Table access
- ✅ Data availability (2022 MAX, 2024 EXP)
- ✅ Date ranges

---

## 📈 Example Output

```
======================================================================
HASSETT FORECASTING SYSTEM
======================================================================
Target: Week 51, 2025
Methodology: 92-93% Accuracy (100+ Experiments)
======================================================================

✅ Connected to Azure Databricks
📊 Loading historical data from Databricks...
✅ Loaded 358,820 records
📅 Date range: 2022-01-01 to 2024-12-31

======================================================================
GENERATING FORECAST: Week 51, 2025
======================================================================

🎄 Seasonal Multiplier: 1.25x
   ⚠️  Peak season week detected!

📊 Step 1: Calculate Baselines
   MAX (2022 Week 51): 12,345 pieces
   EXP (2024 Week 51): 4,789 pieces

📈 Step 2: Calculate YoY Trends
   MAX Trend: 1.050 (↑ 5.0%)
   EXP Trend: 0.980 (↓ 2.0%)

🎯 Step 3: Generate Forecast

📊 Forecast Summary:
ProductType  baseline  forecast  change_%
MAX          12345.0   16156.0      31.0
EXP           4789.0    5876.0      22.7

✅ Total Forecast: 22,032 pieces

💾 Forecast saved to: forecast_week_51_2025_20251212_143022.csv
   Records: 1,847
   Size: 156.3 KB

======================================================================
DETAILED FORECAST SUMMARY
======================================================================

📦 By Product Type:
   MAX:       16,156 pieces (73.3%)
   EXP:        5,876 pieces (26.7%)

📍 Top 10 ODCs:
    1. LAX  :        4,234 pieces (19.2%)
    2. EWR  :        3,567 pieces (16.2%)
    3. IAD  :        2,890 pieces (13.1%)
    4. SLC  :        2,345 pieces (10.6%)
    5. ATL  :        1,678 pieces ( 7.6%)
    ...

📅 By Day of Week:
   Monday   :        2,203 pieces (10.0%)
   Tuesday  :        6,609 pieces (30.0%)
   Wednesday:        6,609 pieces (30.0%)
   Thursday :        6,609 pieces (30.0%)
   Friday   :            0 pieces ( 0.0%)
   Saturday :            0 pieces ( 0.0%)
   Sunday   :            0 pieces ( 0.0%)

======================================================================
✅ FORECAST COMPLETE!
======================================================================
```

---

## 🔧 Advanced Usage

### Generate Multiple Weeks at Once

```bash
# Forecast Weeks 48-52 (Holiday season)
for week in {48..52}; do
    python src/forecast.py --week $week --year 2025 --output forecasts/week_${week}.csv
done
```

### Save to Custom Location

```bash
python src/forecast.py --week 51 --year 2025 --output /path/to/my_forecast.csv
```

### Skip Detailed Summary (Faster)

```bash
python src/forecast.py --week 51 --year 2025 --no-summary
```

---

## 📁 File Structure

```
hassett-forecasting/
├── src/
│   └── forecast.py ⭐ Main forecasting script
├── notebooks/
│   ├── 00_setup_and_test.ipynb ✅ Working
│   └── 01_quick_forecast.ipynb ⭐ Interactive demo
├── docs/
│   └── META_ANALYSIS_100_EXPERIMENTS.md 📊 Methodology
├── test_forecast.py 🧪 Test script
├── run_forecast.sh ⚡ Quick run script
├── QUICKSTART.md 📖 Detailed guide
└── READY_TO_RUN.md 👈 You are here
```

---

## 🎯 Methodology (92-93% Accuracy)

Based on 100+ experiments, the winning approach:

1. **Product-Specific Baselines**
   - MAX: Use 2022 Week N (93.46% accuracy)
   - EXP: Use 2024 Week N (86.37% accuracy)

2. **YoY Trend Adjustment**
   - Compare recent 8 weeks to same period last year
   - Calculate growth multiplier

3. **Seasonal Adjustment** (Fourier-based)
   - Week 48: 1.20x (Thanksgiving)
   - Week 49: 1.25x (Pre-peak)
   - Week 50: 1.27x (Peak - 2 weeks before Christmas)
   - Week 51: 1.25x (Peak - 1 week before Christmas)
   - Week 52: 1.15x (Christmas week)

4. **Day-Level Distribution**
   - Historical day-of-week patterns
   - Monday: Holiday pattern (8% of volume)
   - Tue-Thu: Same-week pattern (92% of volume)

**Formula:**
```
Forecast = Baseline × YoY_Trend × Seasonal_Multiplier
```

---

## 💡 Tips

1. **Run weekly** - Update forecasts as new data arrives
2. **Validate results** - Compare forecasts with actuals
3. **Archive outputs** - Keep CSV files for audit trail
4. **Monitor accuracy** - Track performance over time
5. **Review outliers** - Investigate ODCs with unusual patterns

---

## ❓ Troubleshooting

### "No module named 'databricks'"
```bash
source venv/bin/activate
pip install databricks-sql-connector
```

### "Authentication failed"
```bash
databricks auth login --host https://adb-434028626745069.9.azuredatabricks.net
```

### "No baseline data found"
- Check if 2022 data exists for MAX
- Check if 2024 data exists for EXP
- Run `python test_forecast.py` to diagnose

---

## 📞 Need Help?

- **Quickstart Guide**: `QUICKSTART.md`
- **Methodology Details**: `docs/META_ANALYSIS_100_EXPERIMENTS.md`
- **Notebook Setup**: `NOTEBOOK_SETUP.md`
- **Project Overview**: `README.md`

---

## ✅ Next Steps

1. **Test the system**
   ```bash
   python test_forecast.py
   ```

2. **Run your first forecast**
   ```bash
   python src/forecast.py --week 51 --year 2025
   ```

3. **Review the output CSV**
   - Open in Excel/Google Sheets
   - Or load in pandas: `pd.read_csv('forecast_week_51_2025_*.csv')`

4. **Set up weekly automation** (optional)
   - Create cron job to run forecasts automatically
   - Email results to stakeholders

---

**🎉 You're ready to start forecasting!**

Expected accuracy: **92-93%** overall (93-94% for MAX, 86-88% for EXP)
