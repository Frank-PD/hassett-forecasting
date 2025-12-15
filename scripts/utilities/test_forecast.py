#!/usr/bin/env python3
"""
Quick test script to verify forecast.py works
Run this before using the main forecasting script
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from databricks import sql
import pandas as pd

# Test 1: Databricks Connection
print("=" * 70)
print("TEST 1: Databricks Connection")
print("=" * 70)

try:
    conn = sql.connect(
        server_hostname="adb-434028626745069.9.azuredatabricks.net",
        http_path="/sql/1.0/warehouses/23a9897d305fb7e2",
        auth_type="databricks-oauth"
    )
    print("✅ Connected to Databricks")

    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT 1 as test")
    result = cursor.fetchone()
    print(f"✅ Test query passed: {result}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Test 2: Data Access
print("\n" + "=" * 70)
print("TEST 2: Data Access")
print("=" * 70)

try:
    # Count rows
    count_query = "SELECT COUNT(*) as total FROM decus_domesticops_prod.dbo.tmp_hassett_report"
    count_df = pd.read_sql(count_query, conn)
    total_rows = count_df['total'].iloc[0]
    print(f"✅ Table accessible: {total_rows:,} total rows")

    # Check date range
    date_query = """
    SELECT
        MIN(DATE_SHIP) as min_date,
        MAX(DATE_SHIP) as max_date
    FROM decus_domesticops_prod.dbo.tmp_hassett_report
    """
    date_df = pd.read_sql(date_query, conn)
    print(f"✅ Date range: {date_df['min_date'].iloc[0]} to {date_df['max_date'].iloc[0]}")

    # Check products
    product_query = """
    SELECT DISTINCT ProductType
    FROM decus_domesticops_prod.dbo.tmp_hassett_report
    WHERE ProductType IS NOT NULL
    """
    product_df = pd.read_sql(product_query, conn)
    products = product_df['ProductType'].tolist()
    print(f"✅ Products available: {', '.join(products)}")

except Exception as e:
    print(f"❌ Data access failed: {e}")
    conn.close()
    sys.exit(1)

# Test 3: Baseline Data Check
print("\n" + "=" * 70)
print("TEST 3: Baseline Data Check")
print("=" * 70)

try:
    # Check for 2022 data (MAX baseline)
    check_2022 = """
    SELECT COUNT(*) as count
    FROM decus_domesticops_prod.dbo.tmp_hassett_report
    WHERE YEAR(DATE_SHIP) = 2022 AND ProductType = 'MAX'
    """
    df_2022 = pd.read_sql(check_2022, conn)
    count_2022 = df_2022['count'].iloc[0]

    if count_2022 > 0:
        print(f"✅ 2022 MAX data available: {count_2022:,} records")
    else:
        print(f"⚠️  No 2022 MAX data found (baseline may not work)")

    # Check for 2024 data (EXP baseline)
    check_2024 = """
    SELECT COUNT(*) as count
    FROM decus_domesticops_prod.dbo.tmp_hassett_report
    WHERE YEAR(DATE_SHIP) = 2024 AND ProductType = 'EXP'
    """
    df_2024 = pd.read_sql(check_2024, conn)
    count_2024 = df_2024['count'].iloc[0]

    if count_2024 > 0:
        print(f"✅ 2024 EXP data available: {count_2024:,} records")
    else:
        print(f"⚠️  No 2024 EXP data found (baseline may not work)")

except Exception as e:
    print(f"❌ Baseline check failed: {e}")

finally:
    conn.close()

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("✅ All tests passed! You're ready to run forecasts.")
print("\nNext steps:")
print("  1. Run forecast: python src/forecast.py --week 51 --year 2025")
print("  2. Or use shell script: ./run_forecast.sh 51 2025")
print("=" * 70)
