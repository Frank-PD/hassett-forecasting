# SUNDAY WEEKLY WORKFLOW

## The Weekly Cycle (Every Sunday)

**Scenario:** It's Sunday, December 14, 2025 (Week 51 starts)

**What happened last week:**
- Last Sunday: Generated forecasts for Week 50
- During Week 50: Shipments occurred
- Friday night: Actual data for Week 50 became available

**What happens THIS Sunday:**
1. ✅ **Review Week 50** - Compare forecasts to actuals, learn from mistakes
2. ✅ **Update routing (if monthly)** - Switch routes to better models
3. ✅ **Forecast Week 51** - Generate forecasts for upcoming week

---

## STEP-BY-STEP SUNDAY WORKFLOW

### STEP 1: Record Last Week's Performance (Week 50)
**When:** Every Sunday, first thing
**Purpose:** Learn from last week's forecasts
**Database Action:** INSERT into `performance_history` and `weekly_summary`

```bash
# Compare last week's forecasts to actuals
# This creates a comparison file with forecast vs actual for each route

python3 compare_forecast_to_actual.py \
  --forecasts data/forecasts/week_50_forecasts.csv \
  --actuals data/actuals/week_50_actuals.csv \
  --output data/performance/week_50_comparison.csv

# Record performance in database
python3 src/performance_tracker.py \
  --action record \
  --week-results data/performance/week_50_comparison.csv \
  --db local_performance_tracking.db
```

**What this does:**
- Reads Week 50 forecasts (generated last Sunday)
- Reads Week 50 actuals (arrived Friday night)
- Calculates error for each model on each route
- **Stores in `performance_history` table** (one row per route/model)
- **Stores in `weekly_summary` table** (aggregated metrics)

**Tables Updated:**
| Table | Action | What's Stored |
|-------|--------|---------------|
| `performance_history` | INSERT | Week 50 errors for every route/model combination |
| `weekly_summary` | INSERT | Week 50 aggregated metrics (avg MAPE, median, etc.) |

---

### STEP 2: Check if Monthly Routing Update Needed
**When:** First Sunday of month (or every 4 weeks)
**Purpose:** Adapt to changing patterns
**Database Action:** UPDATE `routing_table` CSV, INSERT into `routing_updates`

```bash
# Check current date
# If it's first Sunday of month OR 4+ weeks since last update...

# Analyze recent performance and update routing table
python3 src/performance_tracker.py \
  --action update \
  --routing-table data/routing_tables/routing_table_current.csv \
  --output data/routing_tables/routing_table_current.csv \
  --lookback-weeks 8 \
  --db local_performance_tracking.db
```

**What this does:**
- **Reads `performance_history`** for last 8 weeks
- For each route: Finds which model had lowest average error
- Compares to current routing table
- If different model is better by >5% → Switch
- **Updates `routing_table_current.csv`** with new model assignments
- **Stores switches in `routing_updates` table**

**Tables Updated:**
| Table | Action | What's Stored |
|-------|--------|---------------|
| `routing_table_current.csv` | UPDATE | New optimal model assignments |
| `routing_updates` | INSERT | Which routes switched and why |

**Example Update:**
```
Route CHI-DET-PKG-3:
  - Last 8 weeks performance:
    - 04_Recent_8W: 18.5% avg error
    - 18_Clustering: 7.2% avg error  ← 11.3% better!
  - Action: Switch from 04_Recent_8W to 18_Clustering
  - Record in routing_updates table
  - Update routing_table_current.csv
```

---

### STEP 3: Generate This Week's Forecasts (Week 51)
**When:** Every Sunday, after optional routing update
**Purpose:** Forecast upcoming week
**Database Action:** READ from `routing_table_current.csv`

```bash
# Generate forecasts for Week 51 using (possibly updated) routing table
python3 run_local_forecast.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data data/historical/all_data.csv \
  --routes-to-forecast routes_week_51.csv \
  --output data/forecasts/week_51_forecasts.csv \
  --week 51 \
  --year 2025
```

**What this does:**
- **Reads `routing_table_current.csv`** (possibly just updated)
- For each route:
  - Looks up optimal model
  - Gets historical data
  - Runs that model
  - Generates forecast
- **Writes to `week_51_forecasts.csv`**

**Tables Used:**
| Table | Action | What's Used |
|-------|--------|-------------|
| `routing_table_current.csv` | READ | Which model to use for each route |
| `data/forecasts/week_51_forecasts.csv` | WRITE | Forecasts for Week 51 |

---

## COMPLETE SUNDAY WORKFLOW SCRIPT

Save this as `sunday_weekly_run.sh`:

```bash
#!/bin/bash
# SUNDAY WEEKLY WORKFLOW
# Run this every Sunday morning to:
# 1. Review last week's performance
# 2. Update routing table (if monthly)
# 3. Generate this week's forecasts

WEEK_LAST=$1      # e.g., 50 (last week)
WEEK_THIS=$2      # e.g., 51 (this week)
YEAR=$3           # e.g., 2025
IS_MONTHLY=$4     # e.g., "yes" or "no"

echo "============================================================"
echo "SUNDAY WORKFLOW - Week $WEEK_THIS, $YEAR"
echo "============================================================"

# STEP 1: Record last week's performance
echo ""
echo "STEP 1: Recording Week $WEEK_LAST performance..."
python3 compare_forecast_to_actual.py \
  --forecasts data/forecasts/week_${WEEK_LAST}_forecasts.csv \
  --actuals data/actuals/week_${WEEK_LAST}_actuals.csv \
  --output data/performance/week_${WEEK_LAST}_comparison.csv

python3 src/performance_tracker.py \
  --action record \
  --week-results data/performance/week_${WEEK_LAST}_comparison.csv \
  --db local_performance_tracking.db

echo "✅ Week $WEEK_LAST performance recorded"

# STEP 2: Monthly routing update (if needed)
if [ "$IS_MONTHLY" = "yes" ]; then
    echo ""
    echo "STEP 2: Monthly routing table update..."

    # Backup current routing table
    cp data/routing_tables/routing_table_current.csv \
       data/routing_tables/routing_table_backup_$(date +%Y%m%d).csv

    # Update routing table
    python3 src/performance_tracker.py \
      --action update \
      --routing-table data/routing_tables/routing_table_current.csv \
      --output data/routing_tables/routing_table_current.csv \
      --lookback-weeks 8 \
      --db local_performance_tracking.db

    echo "✅ Routing table updated based on last 8 weeks"
else
    echo ""
    echo "STEP 2: Skipping routing update (not monthly)"
fi

# STEP 3: Generate this week's forecasts
echo ""
echo "STEP 3: Generating Week $WEEK_THIS forecasts..."
python3 run_local_forecast.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data data/historical/all_data.csv \
  --routes-to-forecast routes_week_${WEEK_THIS}.csv \
  --output data/forecasts/week_${WEEK_THIS}_forecasts.csv \
  --week $WEEK_THIS \
  --year $YEAR

echo "✅ Week $WEEK_THIS forecasts generated"

# STEP 4: Summary
echo ""
echo "============================================================"
echo "✅ SUNDAY WORKFLOW COMPLETE"
echo "============================================================"
echo ""
echo "Generated files:"
echo "  - data/performance/week_${WEEK_LAST}_comparison.csv"
echo "  - data/forecasts/week_${WEEK_THIS}_forecasts.csv"
if [ "$IS_MONTHLY" = "yes" ]; then
    echo "  - data/routing_tables/routing_table_current.csv (UPDATED)"
fi
echo ""
echo "Database updated:"
echo "  - performance_history: Week $WEEK_LAST errors stored"
echo "  - weekly_summary: Week $WEEK_LAST metrics stored"
if [ "$IS_MONTHLY" = "yes" ]; then
    echo "  - routing_updates: Model switches recorded"
fi
echo ""
echo "Next steps:"
echo "  1. Review data/forecasts/week_${WEEK_THIS}_forecasts.csv"
echo "  2. Deploy forecasts to downstream systems"
echo "  3. Next Sunday: Run with week $WEEK_THIS and week $((WEEK_THIS+1))"
```

---

## USAGE EXAMPLES

### Regular Sunday (No Routing Update)
```bash
# Sunday December 14, 2025 - Week 51
bash sunday_weekly_run.sh 50 51 2025 no
```

### First Sunday of Month (With Routing Update)
```bash
# Sunday January 5, 2025 - Week 2 (first Sunday of month)
bash sunday_weekly_run.sh 1 2 2025 yes
```

---

## TABLE UPDATE SCHEDULE

| Table | Update Frequency | Action | Purpose |
|-------|-----------------|--------|---------|
| **performance_history** | Every Sunday | INSERT | Store last week's errors |
| **weekly_summary** | Every Sunday | INSERT | Store last week's metrics |
| **routing_table_current.csv** | First Sunday of month | UPDATE | Switch routes to better models |
| **routing_updates** | First Sunday of month | INSERT | Document model switches |

---

## DATA FLOW DIAGRAM

```
SUNDAY MORNING (Week 51 starts)
═══════════════════════════════

┌──────────────────────────────────┐
│  Week 50 Actuals Arrive          │
│  (Friday night)                  │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  STEP 1: Compare to Week 50      │
│  Forecasts (from last Sunday)    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  INSERT → performance_history    │
│  INSERT → weekly_summary         │
│  (Week 50 errors stored)         │
└────────────┬─────────────────────┘
             │
             ▼
      Is it monthly?
             │
    ┌────────┴────────┐
   YES              NO
    │                │
    ▼                │
┌────────────────┐   │
│ STEP 2:        │   │
│ READ last 8    │   │
│ weeks from     │   │
│ performance_   │   │
│ history        │   │
└───────┬────────┘   │
        │            │
        ▼            │
┌────────────────┐   │
│ UPDATE         │   │
│ routing_table_ │   │
│ current.csv    │   │
└───────┬────────┘   │
        │            │
        ▼            │
┌────────────────┐   │
│ INSERT →       │   │
│ routing_       │   │
│ updates        │   │
└───────┬────────┘   │
        │            │
        └────────┬───┘
                 │
                 ▼
┌──────────────────────────────────┐
│  STEP 3: Generate Week 51        │
│  Forecasts                       │
│  READ → routing_table_current    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│  WRITE → week_51_forecasts.csv   │
│  (Ready for deployment)          │
└──────────────────────────────────┘
```

---

## KEY INSIGHTS

### 1. Routing Table is READ for Forecasting
The `routing_table_current.csv` tells you which model to use for each route.
- **Read every Sunday** when generating forecasts
- **Updated monthly** based on recent performance

### 2. Performance History is WRITTEN for Learning
The `performance_history` table stores errors to learn from.
- **Written every Sunday** after actuals arrive
- **Read monthly** to update routing table

### 3. The Feedback Loop
```
Forecast Week N → Actual Week N arrives → Store errors →
Analyze errors (monthly) → Update routing table →
Forecast Week N+1 with better models → ...
```

### 4. Tables Never Deleted, Only Appended
- `performance_history`: Grows every week (new rows added)
- `routing_updates`: Grows monthly (when routes switch)
- `weekly_summary`: Grows every week (one row per week)
- `routing_table_current.csv`: Gets UPDATED (not appended)

---

## MONTHLY CYCLE EXAMPLE

**Week 48 (Sunday):**
- Record Week 47 performance → `performance_history`
- Generate Week 48 forecasts → Use current `routing_table`

**Week 49 (Sunday):**
- Record Week 48 performance → `performance_history`
- Generate Week 49 forecasts → Use current `routing_table`

**Week 50 (Sunday):**
- Record Week 49 performance → `performance_history`
- Generate Week 50 forecasts → Use current `routing_table`

**Week 51 (Sunday) - MONTHLY UPDATE:**
- Record Week 50 performance → `performance_history`
- **Analyze Weeks 47-50** (last 4 weeks)
- **UPDATE `routing_table`** if routes should switch
- **Record switches** → `routing_updates`
- Generate Week 51 forecasts → Use **NEW** `routing_table`

**Week 52 (Sunday):**
- Record Week 51 performance → `performance_history`
- Generate Week 52 forecasts → Use updated `routing_table`

---

## AZURE DATA FACTORY EQUIVALENT

This Sunday workflow maps directly to ADF:

| Local Script | ADF Component |
|-------------|---------------|
| `sunday_weekly_run.sh` | ADF Pipeline: "Weekly_Forecast_Pipeline" |
| STEP 1: Record performance | ADF Pipeline: "Performance_Tracking" (runs Monday) |
| STEP 2: Update routing | ADF Pipeline: "Monthly_Routing_Update" (runs first Monday) |
| STEP 3: Generate forecasts | ADF Pipeline: "Daily_Forecast" (runs Sunday) |

**ADF Schedule:**
- Sunday 6 AM: Run forecasts for upcoming week
- Monday 6 AM: Record last week's performance
- First Monday 8 AM: Update routing table

---

## QUICK REFERENCE

**Every Sunday:**
```bash
bash sunday_weekly_run.sh <last_week> <this_week> <year> no
```

**First Sunday of Month:**
```bash
bash sunday_weekly_run.sh <last_week> <this_week> <year> yes
```

**Check what was updated:**
```bash
# See last week's errors
sqlite3 local_performance_tracking.db \
  "SELECT * FROM weekly_summary ORDER BY week_number DESC LIMIT 5;"

# See recent routing updates (if monthly)
sqlite3 local_performance_tracking.db \
  "SELECT * FROM routing_updates ORDER BY timestamp DESC LIMIT 10;"
```

---

## SUCCESS METRICS

After each Sunday run, you should see:
- ✅ `performance_history` has new rows (routes × models from last week)
- ✅ `weekly_summary` has new row for last week
- ✅ `routing_table` updated (if monthly)
- ✅ New forecasts generated for this week

**Your system is learning and adapting!** 🎯
