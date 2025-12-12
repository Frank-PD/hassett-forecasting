# Forecasting Models Guide

## 🎯 Three Forecasting Models Available

You have **3 different forecasting scripts** to choose from, each with increasing complexity:

---

## 1️⃣ Baseline Only (`forecast_baseline.py`)

**Simplest approach - just historical baseline**

### How it works:
- MAX: Use 2022 Week N as-is
- EXP: Use 2024 Week N as-is
- **NO adjustments, NO trends, NO seasonal multipliers**

### Expected Accuracy:
- MAX: **93.46%**
- EXP: **86.37%**
- Overall: **92-93%**

### When to use:
- ✅ You want the simplest, most stable forecast
- ✅ Business is steady with no major growth/decline
- ✅ You need a quick baseline estimate

### Run it:
```bash
python src/forecast_baseline.py --week 51 --year 2025
```

### Output filename:
```
baseline_week_51_2025_20251212_143022.csv
```

---

## 2️⃣ Baseline + YoY Trend (`forecast_trend.py`)

**Adds growth/decline adjustment**

### How it works:
1. Get baseline (2022 MAX, 2024 EXP)
2. Calculate YoY trend (recent 8 weeks vs same period last year)
3. Apply: **Forecast = Baseline × Trend**

### Expected Accuracy:
- Better than baseline if clear trend exists
- Captures growth or decline momentum

### When to use:
- ✅ You're seeing recent growth or decline
- ✅ Want to capture YoY momentum
- ✅ Regular (non-peak) weeks

### Run it:
```bash
python src/forecast_trend.py --week 51 --year 2025
```

### Output filename:
```
trend_week_51_2025_20251212_143022.csv
```

### Example output:
```
MAX Trend: 1.050 (↑ 5.0%)
EXP Trend: 0.980 (↓ 2.0%)

Total Forecast: 18,500 pieces
(vs 17,200 baseline = +7.6% change)
```

---

## 3️⃣ Full Integrated (`forecast_integrated.py`)

**Complete system - all adjustments applied**

### How it works:
1. Get baseline (2022 MAX, 2024 EXP)
2. Calculate YoY trend
3. Apply seasonal multiplier (1.25x for Week 51)
4. **Forecast = Baseline × Trend × Seasonal**

### Expected Accuracy:
- **92-93%** overall with all adjustments
- Best for peak season weeks

### When to use:
- ✅ **Peak season weeks (48-52)** ⭐ RECOMMENDED
- ✅ Want most comprehensive forecast
- ✅ Need to account for holiday patterns

### Run it:
```bash
python src/forecast_integrated.py --week 51 --year 2025
```

### Output filename:
```
integrated_week_51_2025_20251212_143022.csv
```

### Seasonal Multipliers:
| Week | Period | Multiplier |
|------|--------|------------|
| 48 | Thanksgiving | 1.20x |
| 49 | Pre-peak | 1.25x |
| 50 | Peak (2 weeks before Xmas) | 1.27x |
| 51 | Peak (1 week before Xmas) | 1.25x |
| 52 | Christmas week | 1.15x |

---

## 🔄 Run All 3 Models at Once

Compare all three approaches side-by-side:

```bash
python run_all_models.py --week 51 --year 2025
```

This will:
1. ✅ Run all 3 models
2. ✅ Generate 3 CSV files
3. ✅ Create comparison report
4. ✅ Show which model to use

### Example comparison output:
```
📊 TOTAL FORECAST VOLUMES:

   1. Baseline Only:           17,134 pieces
   2. Baseline + Trend:        18,500 pieces (vs Baseline: +8.0%)
   3. Full Integrated:         23,125 pieces (vs Baseline: +35.0%)

📦 BY PRODUCT TYPE:

   MAX:
      Baseline:        12,345 pieces
      + Trend:         12,962 pieces
      + Seasonal:      16,203 pieces

   EXP:
      Baseline:         4,789 pieces
      + Trend:          5,538 pieces
      + Seasonal:       6,922 pieces

⭐ RECOMMENDED: Full Integrated
   Reason: Week 51 is peak season - seasonal adjustment needed
```

---

## 📊 Output Files Comparison

All models output CSV files with these columns:

### Baseline Only:
| Column | Description |
|--------|-------------|
| ODC | Origin Distribution Center |
| DDC | Destination Distribution Center |
| dayofweek | 0=Monday, 6=Sunday |
| **forecast** | Final forecast (pieces) ⭐ |
| ProductType | MAX or EXP |
| baseline_year | 2022 (MAX) or 2024 (EXP) |
| method | "Baseline_Only" |
| week | Target week |
| year | Target year |

### Baseline + Trend:
Includes everything above, plus:
| Column | Description |
|--------|-------------|
| baseline | Historical baseline volume |
| trend | YoY growth multiplier (e.g., 1.05 = +5%) |

### Full Integrated:
Includes everything above, plus:
| Column | Description |
|--------|-------------|
| seasonal | Seasonal multiplier (e.g., 1.25x) |

---

## 🎯 Quick Decision Guide

### For Week 51 (1 week before Christmas):

```
❓ Which model should I use?

├─ Just need a quick estimate?
│  └─ ✅ Use BASELINE ONLY
│     python src/forecast_baseline.py --week 51 --year 2025
│
├─ Seeing recent growth/decline?
│  └─ ✅ Use BASELINE + TREND
│     python src/forecast_trend.py --week 51 --year 2025
│
└─ Peak season week (48-52)?
   └─ ⭐ Use FULL INTEGRATED (RECOMMENDED)
      python src/forecast_integrated.py --week 51 --year 2025
```

### For Regular Weeks (1-47, 53):

```
❓ Which model should I use?

├─ Want simplest forecast?
│  └─ ✅ Use BASELINE ONLY
│
├─ Want to capture trends?
│  └─ ⭐ Use BASELINE + TREND (RECOMMENDED)
│
└─ Want all features?
   └─ ✅ Use FULL INTEGRATED
      (Note: seasonal = 1.0x for non-peak weeks)
```

---

## 💡 Recommendations by Week

| Weeks | Recommended Model | Reason |
|-------|------------------|--------|
| 1-47 | **Baseline + Trend** | Captures growth, no seasonal needed |
| 48-52 | **Full Integrated** | Peak season - seasonal critical |
| 53 | **Baseline + Trend** | Back to normal, trend helps |

---

## 🧪 Testing the Models

Test all models before production use:

```bash
# Test each individually
python src/forecast_baseline.py --week 51 --year 2025
python src/forecast_trend.py --week 51 --year 2025
python src/forecast_integrated.py --week 51 --year 2025

# Or test all at once
python run_all_models.py --week 51 --year 2025
```

---

## 📈 Example Comparison (Week 51)

Based on historical testing:

```
Scenario: Week 51, 2025 (Peak Season)

Model 1 - Baseline Only:
  Total: 17,134 pieces
  Pros: Simple, stable
  Cons: Misses peak season surge

Model 2 - Baseline + Trend:
  Total: 18,500 pieces (+8.0%)
  Pros: Captures growth
  Cons: Still misses seasonal peak

Model 3 - Full Integrated:
  Total: 23,125 pieces (+35.0%)
  Pros: Captures peak season (1.25x)
  Cons: More complex

⭐ WINNER for Week 51: Full Integrated
   Actual historical accuracy: 92-93%
```

---

## 📁 File Organization

All forecast outputs go to the current directory by default:

```
hassett-forecasting/
├── baseline_week_51_2025_timestamp.csv
├── trend_week_51_2025_timestamp.csv
├── integrated_week_51_2025_timestamp.csv
└── forecasts/
    └── comparison_week_51_2025_timestamp.csv
```

Organize by week:
```bash
mkdir -p forecasts/week_51
python run_all_models.py --week 51 --year 2025 --output-dir forecasts/week_51
```

---

## 🔍 Interpreting Results

### Baseline vs Trend Difference > 10%?
- **Strong YoY trend** detected
- Consider investigating: new routes, business changes, market shifts

### Integrated vs Trend Difference Large?
- **Seasonal effect** is significant
- Normal for weeks 48-52 (peak season)

### All Models Similar?
- **Steady state** business
- Any model will work well

---

## 📞 Need Help?

- **Full methodology**: `docs/META_ANALYSIS_100_EXPERIMENTS.md`
- **Quick start**: `QUICKSTART.md`
- **Ready to run**: `READY_TO_RUN.md`

---

**TL;DR:**
- Peak season (weeks 48-52)? → Use **Full Integrated**
- Regular weeks? → Use **Baseline + Trend**
- Quick estimate? → Use **Baseline Only**
- Not sure? → Run **all 3** with `run_all_models.py`
