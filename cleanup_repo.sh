#!/bin/bash
# REPO CLEANUP SCRIPT
# Organizes all files into proper directories

echo "=================================================================="
echo "HASSETT FORECASTING - REPOSITORY CLEANUP"
echo "=================================================================="
echo ""

# Create archive directory for old test outputs
mkdir -p archive/old_forecasts
mkdir -p archive/old_comparisons
mkdir -p archive/old_logs

echo "📁 Creating directory structure..."

# Archive old forecast test files (week 50 tests from Dec 12)
echo ""
echo "🗄️  Archiving old Week 50 test forecasts..."
mv baseline_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived baseline forecasts"
mv ensemble_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived ensemble forecasts"
mv final_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived final forecasts"
mv hybrid_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived hybrid forecasts"
mv improved_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived improved forecasts"
mv integrated_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived integrated forecasts"
mv lane_adaptive_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived lane adaptive forecasts"
mv ml_forecast_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived ML forecasts"
mv optimal_forecast_week_50_*.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived optimal forecasts"
mv best_model_per_route_forecast_week50.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived best model forecasts"

# Archive old comparison files
echo ""
echo "🗄️  Archiving old comparison files..."
mv *vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null && echo "   ✓ Archived comparison files"
mv ensemble_vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null
mv forecast_vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null
mv hybrid_vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null
mv ml_vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null
mv optimal_vs_actuals_comparison.csv archive/old_comparisons/ 2>/dev/null
mv lane_adaptive_vs_actuals.csv archive/old_comparisons/ 2>/dev/null

# Archive old side-by-side comparison
echo ""
echo "🗄️  Archiving old multi-model outputs..."
mv all_models_comparison_side_by_side.csv archive/old_comparisons/ 2>/dev/null && echo "   ✓ Archived side-by-side comparison"
mv multi_model_results_*.csv archive/old_comparisons/ 2>/dev/null && echo "   ✓ Archived multi-model results"

# Archive logs
echo ""
echo "🗄️  Archiving log files..."
mv comprehensive_run.log archive/old_logs/ 2>/dev/null && echo "   ✓ Archived comprehensive run log"
mv *.log archive/old_logs/ 2>/dev/null

# Archive temporary test files
echo ""
echo "🗄️  Archiving temporary test files..."
mv local_forecasts_test.csv archive/old_forecasts/ 2>/dev/null && echo "   ✓ Archived local test file"

# Keep production files - show what stays
echo ""
echo "=================================================================="
echo "✅ CLEANUP COMPLETE"
echo "=================================================================="
echo ""
echo "📂 PRODUCTION FILES (kept in place):"
echo ""

# List what remains
echo "Root directory scripts:"
ls -lh *.py *.sh 2>/dev/null | grep -v cleanup_repo.sh | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "Current week data:"
ls -lh comprehensive_week51.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
ls -lh production_forecast_week51.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "Week 50 production files (kept for reference):"
ls -lh comprehensive_all_models_week50.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
ls -lh production_forecast_week50_DEMO.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "Routing tables:"
ls -lh route_model_routing_table*.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "Route lists:"
ls -lh routes_week_*.csv 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "Documentation:"
ls -lh deployment_summary.txt 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
ls -lh *.md 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo "📂 Archived files moved to:"
echo "   - archive/old_forecasts/ (test forecast outputs)"
echo "   - archive/old_comparisons/ (comparison files)"
echo "   - archive/old_logs/ (log files)"
echo ""

# Count archived files
ARCHIVED_FORECASTS=$(ls -1 archive/old_forecasts/ 2>/dev/null | wc -l)
ARCHIVED_COMPARISONS=$(ls -1 archive/old_comparisons/ 2>/dev/null | wc -l)
ARCHIVED_LOGS=$(ls -1 archive/old_logs/ 2>/dev/null | wc -l)
TOTAL_ARCHIVED=$((ARCHIVED_FORECASTS + ARCHIVED_COMPARISONS + ARCHIVED_LOGS))

echo "📊 Cleanup Summary:"
echo "   Archived forecasts: $ARCHIVED_FORECASTS files"
echo "   Archived comparisons: $ARCHIVED_COMPARISONS files"
echo "   Archived logs: $ARCHIVED_LOGS files"
echo "   Total archived: $TOTAL_ARCHIVED files"
echo ""
echo "✅ Repository is now organized and clean!"
echo ""
