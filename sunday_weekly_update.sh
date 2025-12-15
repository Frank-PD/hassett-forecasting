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

# Prepare routes to forecast
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
  --historical-data "/Users/frankgiles/Downloads/data 4.csv" \
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
echo ""
echo "🔄 Next Steps:"
echo "   1. Review data/forecasts/week_${WEEK_THIS}_forecasts.csv"
echo "   2. Deploy forecasts to downstream systems"
echo "   3. Next Sunday: ./sunday_weekly_update.sh $WEEK_THIS $((WEEK_THIS+1)) $YEAR $LOOKBACK"
echo ""
