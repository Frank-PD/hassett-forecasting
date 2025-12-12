#!/bin/bash
# Quick Forecast Runner
# Usage: ./run_forecast.sh 51 2025

set -e

# Activate virtual environment
source venv/bin/activate

# Default values
WEEK=${1:-51}
YEAR=${2:-2025}

echo "🚀 Running Hassett Forecast..."
echo "   Week: $WEEK"
echo "   Year: $YEAR"
echo ""

# Run forecast
python src/forecast.py --week $WEEK --year $YEAR

echo ""
echo "✅ Done! Check the generated CSV file."
