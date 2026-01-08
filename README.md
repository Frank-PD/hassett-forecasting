# Hassett Forecasting System
**Adaptive ensemble forecasting for logistics package volume prediction**

## Overview

Production-ready forecasting system using 14 competing models with adaptive model routing. The system automatically learns which forecasting approach works best for each route through continuous performance tracking.

### Key Features
- **14 Forecasting Models**: Traditional, SARIMA, ML, clustering, and adaptive approaches
- **Route-Level Intelligence**: Each route automatically selects its best-performing model
- **Continuous Learning**: SQLite-based performance tracking and routing table updates
- **Production Ready**: Designed for Azure Data Lake deployment

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Databricks Data Source                     │
│  (decus_domesticops_prod.dbo.tmp_hassett)  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  14 Competing Models                        │
├─────────────────────────────────────────────┤
│  01. Historical Baseline                    │
│  02. Recent 2-Week Average                  │
│  03. Recent 4-Week Average                  │
│  04. Recent 8-Week Average                  │
│  05. Trend Adjusted                         │
│  06. Prior Week                             │
│  07. Same Week Last Year                    │
│  08. Week-Specific Historical               │
│  09. Exponential Smoothing                  │
│  10. Probabilistic                          │
│  11. Hybrid Week Blend                      │
│  12. Median Recent                          │
│  13. Weighted Recent Week                   │
│  14. SARIMA (52-week seasonality)           │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Performance Tracker (SQLite)               │
│  - Tracks forecast vs actual errors         │
│  - Rolling 4-8 week performance windows     │
│  - Identifies best model per route          │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Adaptive Routing Table                     │
│  - Route → Best Model assignment            │
│  - Automatically updated weekly             │
│  - Confidence scoring                       │
└─────────────────────────────────────────────┘
```

---

## Repository Structure

```
hassett-forecasting/
├── src/
│   ├── forecast_comprehensive_all_models.py  # 14 forecasting models
│   └── performance_tracker.py                # Performance tracking system
│
├── data/
│   ├── performance/                          # SQLite database
│   ├── forecasts/                            # Generated forecasts
│   └── routing_tables/                       # Model routing assignments
│
├── backfill_training_data.py                 # Backfill historical data (one-time)
├── run_comprehensive_update.py               # Weekly production run
├── requirements.txt                          # Python dependencies
└── README.md                                 # This file
```

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <your-azure-devops-url>
cd hassett-forecasting

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initial Setup (One-Time)

Backfill historical data to train the system:

```bash
python3 backfill_training_data.py --weeks 10
```

This will:
- Run all 14 models on past 10 weeks of data
- Populate the SQLite performance tracking database
- Take ~4-6 hours (includes SARIMA which is slow)

**Tip**: Use `--skip-sarima` flag for faster testing

### 3. Weekly Production Run

```bash
python3 run_comprehensive_update.py
```

This will:
1. Generate forecasts for next week using all 14 models
2. Compare with actuals (if available)
3. Update performance tracking database
4. Update routing table with best models per route
5. Output forecast CSV and routing table CSV

---

## Azure Deployment

### Option A: Azure Data Factory

1. **Upload files** to Azure Data Lake Storage
2. **Create pipeline** with Python Script activity
3. **Schedule**: Weekly trigger (every Monday)
4. **Script**: `run_comprehensive_update.py`
5. **Persist**: Mount Data Lake storage for SQLite database

### Option B: Azure Databricks

1. **Upload** `/src` folder to Databricks workspace
2. **Create job** running `run_comprehensive_update.py`
3. **Schedule**: Weekly cluster trigger
4. **Output**: Write results to Delta tables

### Configuration

Update Databricks connection in scripts:
```python
DATABRICKS_CONFIG = {
    "server_hostname": "your-databricks-instance",
    "http_path": "/sql/1.0/warehouses/your-warehouse",
    "auth_type": "databricks-oauth"  # or use Service Principal
}
```

---

## How It Works

### Adaptive Model Selection

1. **Every week**: Run all 14 models on every route
2. **Track performance**: Record actual vs forecast errors
3. **Rolling evaluation**: Assess model performance over last 4-8 weeks
4. **Automatic routing**: Assign best-performing model to each route
5. **Continuous learning**: System improves over time

### Route Intelligence

Different routes have different characteristics:
- **Volatile e-commerce routes** → Recent trend models win
- **Stable B2B routes** → Historical baseline wins
- **Seasonal routes** → SARIMA or year-over-year models win
- **Growing markets** → Trend-adjusted models win

### Confidence Scoring

Each forecast includes confidence level based on historical error rate:
- **HIGH**: Error ≤ 20% - Trust this forecast
- **MEDIUM**: Error ≤ 50% - Reasonable forecast
- **LOW**: Error > 50% - Use ensemble of top 3 models for better coverage

Routes with LOW confidence automatically use an ensemble blend of the top 3 models instead of a single model

---

## Key Files

| File | Purpose |
|------|---------|
| `src/forecast_comprehensive_all_models.py` | Contains all 14 forecasting model implementations |
| `src/performance_tracker.py` | SQLite-based performance tracking and routing updates |
| `backfill_training_data.py` | Populate historical training data (run once) |
| `run_comprehensive_update.py` | Main weekly production script |
| `data/performance/performance_tracking.db` | SQLite database with historical performance |
| `data/routing_tables/routing_table_*.csv` | Current model assignments per route |
| `data/forecasts/forecast_*.csv` | Generated forecast outputs |

---

## Dependencies

- **pandas**: Data manipulation
- **numpy**: Numerical operations
- **scikit-learn**: Machine learning models
- **statsmodels**: SARIMA time series model
- **databricks-sql-connector**: Azure Databricks integration
- **tqdm**: Progress bars

---

## Support

Frank Giles

---

## License

Internal use only - Proprietary
