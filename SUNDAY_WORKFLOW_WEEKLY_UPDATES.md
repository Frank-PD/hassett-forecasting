# SUNDAY WORKFLOW - WEEKLY UPDATES (MAXIMUM FRESHNESS)

## Philosophy: Update Everything Every Sunday

**Goal:** Maximum data freshness and rapid adaptation
**Frequency:** ALL tables update EVERY Sunday
**Benefit:** Routes switch to better models immediately, not monthly

---

## EVERY SUNDAY WORKFLOW

**Scenario:** Sunday, December 14, 2025 (Week 51 starts)

**What happens:**
1. ✅ Record Week 50 performance → Update `performance_history` & `weekly_summary`
2. ✅ Analyze recent performance (last 4-8 weeks) → Update `routing_table` if needed
3. ✅ Generate Week 51 forecasts → Use freshest `routing_table`

**All tables refresh EVERY Sunday for maximum freshness!**

---

## COMPLETE SUNDAY SCRIPT

Save as `sunday_weekly_update.sh`:

```bash
#!/bin/bash
# SUNDAY WEEKLY UPDATE - ALL TABLES REFRESH
# Run every Sunday for maximum data freshness

WEEK_LAST=$1      # e.g., 50 (last week)
WEEK_THIS=$2      # e.g., 51 (this week)
YEAR=$3           # e.g., 2025
LOOKBACK=$4       # e.g., 8 (how many weeks to analyze, default 8)

# Default lookback to 8 weeks
LOOKBACK=${LOOKBACK:-8}

echo "============================================================"
echo "SUNDAY WEEKLY UPDATE - Week $WEEK_THIS, $YEAR"
echo "Maximum Data Freshness Mode: ALL TABLES UPDATE"
echo "============================================================"
echo ""
echo "Analyzing last $LOOKBACK weeks of performance"
echo ""

# ============================================================
# STEP 1: Record Last Week's Performance
# ============================================================
echo "STEP 1: Recording Week $WEEK_LAST performance..."
echo "-----------------------------------------------------------"

# Compare forecasts to actuals
python3 compare_forecast_to_actual.py \
  --forecasts data/forecasts/week_${WEEK_LAST}_forecasts.csv \
  --actuals data/actuals/week_${WEEK_LAST}_actuals.csv \
  --output data/performance/week_${WEEK_LAST}_comparison.csv

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to compare forecasts to actuals"
    exit 1
fi

# Store in database
python3 src/performance_tracker.py \
  --action record \
  --week-results data/performance/week_${WEEK_LAST}_comparison.csv \
  --db local_performance_tracking.db

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to record performance in database"
    exit 1
fi

echo "✅ Week $WEEK_LAST performance recorded"
echo "   Tables updated:"
echo "   - performance_history: Week $WEEK_LAST errors stored"
echo "   - weekly_summary: Week $WEEK_LAST metrics stored"
echo ""

# ============================================================
# STEP 2: Update Routing Table (EVERY WEEK)
# ============================================================
echo "STEP 2: Updating routing table based on last $LOOKBACK weeks..."
echo "-----------------------------------------------------------"

# Backup current routing table
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp data/routing_tables/routing_table_current.csv \
   data/routing_tables/backup/routing_table_${BACKUP_DATE}.csv

echo "✅ Backed up current routing table"

# Analyze recent performance and update routing table
python3 src/performance_tracker.py \
  --action update \
  --routing-table data/routing_tables/routing_table_current.csv \
  --output data/routing_tables/routing_table_current.csv \
  --lookback-weeks $LOOKBACK \
  --db local_performance_tracking.db

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to update routing table"
    # Restore backup
    cp data/routing_tables/backup/routing_table_${BACKUP_DATE}.csv \
       data/routing_tables/routing_table_current.csv
    echo "⚠️  Restored routing table from backup"
    exit 1
fi

echo "✅ Routing table updated based on last $LOOKBACK weeks"
echo "   Tables updated:"
echo "   - routing_table_current.csv: Model assignments refreshed"
echo "   - routing_updates: Route switches documented"
echo ""

# Show routing update summary
echo "📊 Routing Update Summary:"
sqlite3 local_performance_tracking.db \
  "SELECT COUNT(*) as switches FROM routing_updates WHERE week_number = $WEEK_THIS AND year = $YEAR;"

# ============================================================
# STEP 3: View Recent Performance Trends
# ============================================================
echo "STEP 3: Checking performance trends..."
echo "-----------------------------------------------------------"

python3 src/performance_tracker.py \
  --action summary \
  --lookback-weeks $LOOKBACK \
  --db local_performance_tracking.db

echo ""

# ============================================================
# STEP 4: Generate This Week's Forecasts
# ============================================================
echo "STEP 4: Generating Week $WEEK_THIS forecasts with fresh routing table..."
echo "-----------------------------------------------------------"

# Prepare routes to forecast (in production, this comes from your system)
# For now, extract all routes from routing table
if [ ! -f "routes_week_${WEEK_THIS}.csv" ]; then
    echo "Creating routes list from routing table..."
    python3 prepare_test_routes.py \
      --routing-table data/routing_tables/routing_table_current.csv \
      --num-routes 0 \
      --output routes_week_${WEEK_THIS}.csv
fi

# Generate forecasts
python3 run_local_forecast.py \
  --routing-table data/routing_tables/routing_table_current.csv \
  --historical-data data/historical/all_data.csv \
  --routes-to-forecast routes_week_${WEEK_THIS}.csv \
  --output data/forecasts/week_${WEEK_THIS}_forecasts.csv \
  --week $WEEK_THIS \
  --year $YEAR

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to generate forecasts"
    exit 1
fi

echo "✅ Week $WEEK_THIS forecasts generated"
echo ""

# ============================================================
# SUMMARY
# ============================================================
echo "============================================================"
echo "✅ SUNDAY WEEKLY UPDATE COMPLETE"
echo "============================================================"
echo ""
echo "📁 Files Updated:"
echo "   - data/performance/week_${WEEK_LAST}_comparison.csv (NEW)"
echo "   - data/routing_tables/routing_table_current.csv (UPDATED)"
echo "   - data/forecasts/week_${WEEK_THIS}_forecasts.csv (NEW)"
echo ""
echo "📊 Database Tables Updated:"
echo "   - performance_history: Week $WEEK_LAST errors"
echo "   - weekly_summary: Week $WEEK_LAST metrics"
echo "   - routing_updates: Route switches (if any)"
echo "   - routing_table: Updated with fresh model assignments"
echo ""
echo "📈 Performance Check:"

# Get Week 50 metrics
sqlite3 local_performance_tracking.db <<EOF
SELECT
  'Week ' || week_number || ': ' ||
  ROUND(average_mape, 1) || '% avg MAPE, ' ||
  routes_under_20pct || '/' || routes_with_actuals || ' routes <20% error'
FROM weekly_summary
WHERE week_number = $WEEK_LAST AND year = $YEAR;
EOF

echo ""
echo "🔄 Next Steps:"
echo "   1. Review data/forecasts/week_${WEEK_THIS}_forecasts.csv"
echo "   2. Deploy forecasts to downstream systems"
echo "   3. Wait for Week $WEEK_THIS actuals (Friday night)"
echo "   4. Next Sunday: Run with week $WEEK_THIS and week $((WEEK_THIS+1))"
echo ""
echo "💡 Routing table is ALWAYS fresh (updated every Sunday)"
echo "   Routes automatically switch to better models as performance improves"
echo ""
```

---

## TABLE UPDATE FREQUENCY (MAXIMUM FRESHNESS)

| Table | Update Frequency | Action | What Happens |
|-------|-----------------|--------|--------------|
| **performance_history** | **EVERY Sunday** | INSERT | Last week's errors stored |
| **weekly_summary** | **EVERY Sunday** | INSERT | Last week's metrics stored |
| **routing_table_current.csv** | **EVERY Sunday** | UPDATE | Routes switch to better models |
| **routing_updates** | **EVERY Sunday** | INSERT | Document route switches |

**ALL TABLES REFRESH WEEKLY FOR MAXIMUM FRESHNESS!**

---

## ADAPTIVE PARAMETERS

Control how aggressive the routing updates are:

```python
# In src/performance_tracker.py update_routing_table() function

# Current settings:
lookback_weeks = 8           # Analyze last 8 weeks
min_weeks = 4                # Need at least 4 weeks of data
improvement_threshold = 5.0  # Switch only if >5% better

# For MORE aggressive adaptation (faster switching):
lookback_weeks = 4           # Analyze last 4 weeks (more recent)
min_weeks = 2                # Only need 2 weeks of data
improvement_threshold = 2.0  # Switch if >2% better

# For LESS aggressive adaptation (more stable):
lookback_weeks = 12          # Analyze last 12 weeks (longer term)
min_weeks = 6                # Need 6 weeks of data
improvement_threshold = 10.0 # Switch only if >10% better
```

---

## EXAMPLE: WEEKLY ADAPTATION IN ACTION

### Week 48 (Sunday)
```bash
bash sunday_weekly_update.sh 47 48 2025 8
```

**What happens:**
- Record Week 47 performance
- Analyze Weeks 40-47 (last 8 weeks)
- Route CHI-DET-PKG-3: 04_Recent_8W averaging 18% error
- Keep current routing table (no switches yet - need 4 weeks minimum)
- Generate Week 48 forecasts

### Week 49 (Sunday)
```bash
bash sunday_weekly_update.sh 48 49 2025 8
```

**What happens:**
- Record Week 48 performance
- Analyze Weeks 41-48 (last 8 weeks)
- Route CHI-DET-PKG-3: 04_Recent_8W averaging 17% error
- Keep current routing table
- Generate Week 49 forecasts

### Week 50 (Sunday)
```bash
bash sunday_weekly_update.sh 49 50 2025 8
```

**What happens:**
- Record Week 49 performance
- Analyze Weeks 42-49 (last 8 weeks)
- Route CHI-DET-PKG-3: 04_Recent_8W averaging 18% error
- Keep current routing table
- Generate Week 50 forecasts

### Week 51 (Sunday) - FIRST ADAPTATION
```bash
bash sunday_weekly_update.sh 50 51 2025 8
```

**What happens:**
- Record Week 50 performance
- Analyze Weeks 43-50 (last 8 weeks, NOW have 4 weeks minimum!)
- Route CHI-DET-PKG-3:
  - 04_Recent_8W: 18.5% average error (last 8 weeks)
  - 18_Clustering: 7.2% average error (last 8 weeks) ← 11.3% better!
- **SWITCH DETECTED**: Update routing table
  - CHI-DET-PKG-3 → 18_Clustering
  - Record in routing_updates table
- Generate Week 51 forecasts **with updated routing table**

### Week 52 (Sunday)
```bash
bash sunday_weekly_update.sh 51 52 2025 8
```

**What happens:**
- Record Week 51 performance
- Analyze Weeks 44-51 (last 8 weeks)
- Route CHI-DET-PKG-3: Now using 18_Clustering
  - Check if 18_Clustering still best (yes, 6.8% average)
  - Keep current assignment
- Check other routes for switches
- Generate Week 52 forecasts

**The system continuously adapts every week!**

---

## BENEFITS OF WEEKLY UPDATES

### ✅ Maximum Responsiveness
- Routes switch to better models immediately (next week)
- No waiting for monthly cycle
- Fastest possible adaptation to pattern changes

### ✅ Always Fresh Data
- Routing table reflects LATEST performance (last 8 weeks)
- Not stale month-old decisions
- Current patterns drive current forecasts

### ✅ Continuous Learning
- System learns every week
- Performance improvements compound
- Bad models get replaced quickly

### ✅ Early Problem Detection
- If a model starts performing poorly, it's replaced next week
- Don't wait a month to fix degrading performance
- Proactive vs reactive

---

## SAFEGUARDS AGAINST INSTABILITY

With weekly updates, you need safeguards to prevent thrashing:

### 1. Minimum Weeks Requirement
```python
min_weeks = 4  # Need at least 4 weeks of data before switching
```
**Why:** Prevents switches based on 1-2 weeks of noise

### 2. Improvement Threshold
```python
improvement_threshold = 5.0  # Switch only if >5% better
```
**Why:** Prevents switching for marginal gains

### 3. Rolling Window
```python
lookback_weeks = 8  # Analyze last 8 weeks
```
**Why:** Averages out weekly volatility

### 4. Switch Cooldown (Optional)
```python
# In performance_tracker.py, add:
# Don't switch if route switched in last 4 weeks
last_switch = get_last_switch_week(route_key)
if current_week - last_switch < 4:
    skip_switch()
```
**Why:** Prevents flip-flopping between models

---

## MONITORING WEEKLY UPDATES

### Check Routing Update Activity
```bash
# How many routes switched this week?
sqlite3 local_performance_tracking.db \
  "SELECT COUNT(*) FROM routing_updates WHERE week_number = 51 AND year = 2025;"

# Which routes switched?
sqlite3 local_performance_tracking.db \
  "SELECT route_key, old_model, new_model, performance_improvement
   FROM routing_updates
   WHERE week_number = 51 AND year = 2025
   ORDER BY performance_improvement DESC
   LIMIT 10;"
```

### Weekly Performance Trend
```bash
# Last 8 weeks performance
sqlite3 local_performance_tracking.db \
  "SELECT week_number,
          ROUND(average_mape, 1) as avg_mape,
          routes_under_20pct || '/' || routes_with_actuals as good_routes
   FROM weekly_summary
   WHERE year = 2025 AND week_number >= 44
   ORDER BY week_number;"
```

### Model Usage Over Time
```bash
# Which models are used most in current routing table?
sqlite3 local_performance_tracking.db \
  "SELECT optimal_model, COUNT(*) as routes
   FROM routing_table_current
   GROUP BY optimal_model
   ORDER BY routes DESC;"
```

---

## USAGE

### Every Sunday:
```bash
# Make script executable (first time only)
chmod +x sunday_weekly_update.sh

# Run with last week and this week
./sunday_weekly_update.sh 50 51 2025 8

# Parameters:
# $1 = Last week (50)
# $2 = This week (51)
# $3 = Year (2025)
# $4 = Lookback weeks (8) - optional, defaults to 8
```

### Alternative: Use different lookback windows
```bash
# Shorter window (more reactive to recent changes)
./sunday_weekly_update.sh 50 51 2025 4

# Longer window (more stable, less reactive)
./sunday_weekly_update.sh 50 51 2025 12
```

---

## COMPARISON: WEEKLY vs MONTHLY UPDATES

| Aspect | Weekly Updates | Monthly Updates |
|--------|---------------|-----------------|
| **Responsiveness** | High (1 week lag) | Lower (4 week lag) |
| **Stability** | Medium (more switches) | High (fewer switches) |
| **Computational Cost** | Higher (weekly) | Lower (monthly) |
| **Data Freshness** | Maximum | Good |
| **Risk of Thrashing** | Medium | Low |
| **Best For** | Dynamic, volatile routes | Stable, predictable routes |

**Recommendation:** Start with **weekly updates** for maximum freshness, adjust if too volatile.

---

## DIRECTORY STRUCTURE

```
data/
├── forecasts/
│   ├── week_50_forecasts.csv
│   └── week_51_forecasts.csv  (NEW every Sunday)
├── actuals/
│   └── week_50_actuals.csv    (Arrives Friday)
├── performance/
│   └── week_50_comparison.csv (NEW every Sunday)
├── historical/
│   └── all_data.csv
└── routing_tables/
    ├── routing_table_current.csv  (UPDATED every Sunday)
    └── backup/
        ├── routing_table_20251207_080000.csv
        └── routing_table_20251214_080000.csv (NEW every Sunday)
```

---

## AUTOMATED SCHEDULING

### Local (cron)
```bash
# Edit crontab
crontab -e

# Add: Run every Sunday at 8 AM
0 8 * * 0 cd /path/to/hassett-forecasting && ./sunday_weekly_update.sh $(date -d 'last week' +\%W) $(date +\%W) $(date +\%Y) 8 >> logs/sunday_run.log 2>&1
```

### Azure Data Factory
```json
{
  "name": "WeeklySundayUpdate",
  "properties": {
    "type": "ScheduleTrigger",
    "typeProperties": {
      "recurrence": {
        "frequency": "Week",
        "interval": 1,
        "schedule": {
          "weekDays": ["Sunday"],
          "hours": [8],
          "minutes": [0]
        }
      }
    }
  }
}
```

---

## SUCCESS CRITERIA

After running for 4+ weeks, you should see:

✅ **All tables updating every Sunday**
```sql
SELECT COUNT(*) FROM weekly_summary WHERE year = 2025;
-- Should equal number of weeks run
```

✅ **Routes switching to better models**
```sql
SELECT COUNT(*) FROM routing_updates WHERE year = 2025;
-- Should have some switches (10-50 per week typical)
```

✅ **Improving performance over time**
```sql
SELECT week_number, average_mape
FROM weekly_summary
WHERE year = 2025
ORDER BY week_number;
-- MAPE should trend downward
```

✅ **Routing table stays fresh**
```bash
ls -lh data/routing_tables/routing_table_current.csv
# Modified date should be this Sunday
```

---

**Your system now has MAXIMUM DATA FRESHNESS with weekly updates to all tables!** 🚀
