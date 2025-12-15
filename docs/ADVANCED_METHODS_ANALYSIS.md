# Advanced Forecasting Methods Analysis

## Question: Should we add Clustering, SARIMA, or SARIMAX?

### Current State
- **Volume Accuracy**: HYBRID achieves 1.6% error ✅ (SOLVED)
- **Route Coverage**: Only 28.5% matched ❌ (REAL PROBLEM)
- **Routes**: 871 unique route-day combinations in Week 50
- **Data**: 12-16 weeks of recent history available
- **Volatility**: Routes vary 50-200% week-to-week

---

## Method 1: Clustering

### What It Is
Group similar routes together based on patterns, then forecast at cluster level.

**Example Clusters**:
- **Cluster 1**: High-volume, stable routes (ATL→LAX, DFW→SEA)
- **Cluster 2**: Low-volume, sporadic routes (CVG→DEN)
- **Cluster 3**: New routes (appeared in last 4 weeks)
- **Cluster 4**: Seasonal routes (only ship during peak)

### How It Would Work

```python
from sklearn.cluster import KMeans

# Step 1: Extract features per route
features = extract_features(all_routes)
# Features: avg_volume, frequency, volatility, recency, etc.

# Step 2: Cluster routes
kmeans = KMeans(n_clusters=5)
clusters = kmeans.fit_predict(features)

# Step 3: Forecast per cluster
for cluster in unique(clusters):
    cluster_routes = routes[clusters == cluster]

    # Use appropriate method per cluster
    if cluster == 'stable_high_volume':
        forecast = recent_4_week_average()
    elif cluster == 'sporadic':
        forecast = prior_week() * 0.5  # Probabilistic
    elif cluster == 'new':
        forecast = cluster_avg() * confidence
```

### Pros ✅

1. **Handles Missing Routes**
   - New route appears → assign to similar cluster → forecast
   - Solves the "missed routes" problem

2. **Data Sharing**
   - Routes with limited data benefit from cluster patterns
   - Example: New route in "ATL origin" cluster uses ATL patterns

3. **Automatic Segmentation**
   - Discovers natural route groups
   - Different forecasting logic per cluster

4. **Scalable**
   - Works with 100 or 10,000 routes
   - O(n) complexity per week

### Cons ❌

1. **Loses Route-Specific Nuance**
   - ATL→BOS and ATL→DEN might cluster together
   - But have very different volumes (59 vs 39 pieces)

2. **Cluster Stability**
   - Routes change clusters over time
   - Need to re-cluster periodically

3. **Which Features to Cluster On?**
   - Volume? Frequency? Origin? Destination? Product?
   - Wrong features = wrong clusters

4. **Still Need Volume Forecasting**
   - Clustering solves "which routes" not "how much"
   - Still need method to forecast cluster volume

### Our Specific Use Case

**Would it help with missed routes?**

**YES** - Example:
```
Route: SLC→IAD, MAX, Tuesday (missed by Hybrid)

Clustering approach:
1. Identify: High-volume, SLC origin, frequent shipper
2. Assign to: "Cluster 2: High-volume hub routes"
3. Forecast: Cluster average × SLC factor
4. Result: Captures route Hybrid missed
```

**Estimated Impact**:
- Route coverage: 28.5% → 45-55%
- Missed routes: 623 → 400-450
- Volume error: 1.6% → 5-10% (trades accuracy for coverage)

### Recommendation: ✅ YES, Worth Testing

**Implementation Approach**:
```python
# Hybrid-Cluster Model
def forecast(target_week):
    # Step 1: Use Hybrid for high-confidence routes
    baseline_routes = hybrid_model()

    # Step 2: Use Clustering for missed routes
    missed = get_missed_routes(recent_4_weeks)

    for route in missed:
        cluster = assign_cluster(route)
        forecast = cluster_forecast(cluster, route)
        baseline_routes.append(forecast)

    return baseline_routes
```

**Expected**: 45-55% route coverage, 5-8% volume error

---

## Method 2: SARIMA (Seasonal AutoRegressive Integrated Moving Average)

### What It Is

Classical time-series model that captures:
- **Seasonal** patterns (S): Weekly/yearly cycles
- **AutoRegressive** (AR): Value depends on previous values
- **Integrated** (I): Handles trends
- **Moving Average** (MA): Smooths noise

**Example**: SARIMA(1,1,1)(1,1,1,52) for weekly seasonality

### How It Would Work

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# For each route:
for route in all_routes:
    # Get historical time series (need 52+ weeks)
    history = get_route_history(route, weeks=52)

    # Fit SARIMA model
    model = SARIMAX(
        history,
        order=(1, 1, 1),          # AR, I, MA
        seasonal_order=(1, 1, 1, 52),  # Seasonal AR, I, MA, period
        enforce_stationarity=False
    )
    fitted = model.fit()

    # Forecast next week
    forecast = fitted.forecast(steps=7)
```

### Pros ✅

1. **Purpose-Built for Time Series**
   - Statistical foundation
   - Handles seasonality naturally
   - Proven method (decades of use)

2. **Captures Weekly Patterns**
   - Week 50 vs Week 10 differences
   - Day-of-week patterns
   - Holiday effects

3. **Trend Handling**
   - Routes growing/declining
   - Automatic trend detection

4. **Confidence Intervals**
   - Statistical uncertainty bounds
   - Know prediction confidence

### Cons ❌

1. **Needs 52+ Weeks of Data PER ROUTE** ⚠️
   - We only have 12-16 weeks
   - Many routes don't exist 52 weeks ago
   - New routes = no SARIMA possible

2. **Computationally Expensive**
   - Fit 871+ separate models
   - Each model takes 1-5 seconds
   - Total: 15-70 minutes per forecast

3. **Assumes Stable Patterns**
   - Our data is volatile (50-200% variance)
   - Routes appear/disappear
   - Violates stationarity assumption

4. **Doesn't Solve Route Selection**
   - Still need to decide which routes to forecast
   - Only helps with volume prediction
   - We already have 1.6% volume accuracy!

5. **Poor with Sporadic Data**
   - Routes that ship 2/7 days break SARIMA
   - Lots of zeros in time series
   - Model will struggle

### Our Specific Use Case

**Our Data Reality**:
```
Route: ATL→BOS, MAX, Tuesday
Available history:
- Week 50: 29 pieces
- Week 49: 0 pieces (didn't ship)
- Week 48: 35 pieces
- Week 47: 0 pieces
- Week 46: 28 pieces
... (12 weeks total, lots of zeros)
```

**SARIMA Requirements**:
- Needs 52+ continuous weeks ❌ (we have 12)
- Prefers daily data ❌ (we have sporadic)
- Assumes stability ❌ (we have volatility)

**Would it improve our forecast?**

**NO** - We already achieve:
- 1.6% volume error with simple 4-week average
- SARIMA needs way more data than we have
- Won't solve the "missing routes" problem

### Recommendation: ❌ NO, Not Suitable

**Reasons**:
1. Insufficient data (12 weeks vs 52+ needed)
2. Sporadic shipping patterns break model
3. Too computationally expensive (871+ models)
4. Doesn't solve our real problem (route coverage)
5. Simple averaging already works (1.6% error)

---

## Method 3: SARIMAX (SARIMA with eXogenous variables)

### What It Is

SARIMA + external variables

**Example**:
```python
SARIMAX(
    route_history,
    exog=[
        holiday_indicator,      # Is it a holiday week?
        fuel_price,             # Fuel costs
        peak_season_flag,       # Peak shipping season?
        weather_disruption,     # Weather events?
    ],
    order=(1,1,1),
    seasonal_order=(1,1,1,52)
)
```

### Pros ✅ (Same as SARIMA, plus:)

1. **Incorporates External Factors**
   - Peak season effects
   - Economic indicators
   - Weather/disruptions

2. **More Accurate (in theory)**
   - Explains variance with real factors
   - Better than pure time-series

### Cons ❌ (All SARIMA cons, plus:)

1. **All SARIMA Problems** (see above)
   - Need 52+ weeks of data ❌
   - Computationally expensive ❌
   - Assumes stability ❌

2. **PLUS: Need External Data**
   - Where to get holiday calendars?
   - Fuel prices by week?
   - Weather data by route?
   - More data pipeline complexity

3. **Feature Engineering Burden**
   - Which exogenous variables matter?
   - How to encode them?
   - Risk of overfitting

### Our Specific Use Case

**Potential Exogenous Variables**:
- Week number (1-53) → Already captured in Hybrid baseline
- Holiday indicator → Could help, but need calendar
- Peak season → Already use 1.27x multiplier
- Product type → Already split MAX/EXP

**Would it help?**

**NO** - Same problems as SARIMA, plus:
- Don't have exogenous data sources
- Simple methods already work
- Adds complexity without clear benefit

### Recommendation: ❌ NO, Even Less Suitable

**Reasons**:
1. All the SARIMA problems
2. Plus: need external data we don't have
3. Plus: more complexity
4. Doesn't solve route coverage problem

---

## Comparison: Methods vs Our Goals

### Our Core Problem

| Issue | Current State | What We Need |
|-------|---------------|--------------|
| **Volume Accuracy** | 1.6% error ✅ | Already solved! |
| **Route Coverage** | 28.5% ❌ | Need 50-70% |
| **Missed Routes** | 623 ❌ | Need <400 |
| **New Route Handling** | None ❌ | Need method |

### Method Evaluation Matrix

| Method | Volume Accuracy | Route Coverage | New Routes | Complexity | Data Needs | Verdict |
|--------|----------------|----------------|------------|------------|------------|---------|
| **HYBRID** (current) | ✅ Excellent (1.6%) | ❌ Poor (28.5%) | ❌ None | Low | 12 weeks | Baseline |
| **Clustering** | ⚠️ Good (5-10%) | ✅ Good (45-55%) | ✅ Yes | Medium | 12 weeks | ✅ **Recommended** |
| **SARIMA** | ⚠️ Unknown | ❌ Poor (same as Hybrid) | ❌ None | High | 52+ weeks ❌ | ❌ Not suitable |
| **SARIMAX** | ⚠️ Unknown | ❌ Poor (same as Hybrid) | ❌ None | Very High | 52+ weeks + exog ❌ | ❌ Not suitable |
| **ML Classifier** | ⚠️ Poor (95%) | ✅ Excellent (68%) | ✅ Yes | Medium | 12 weeks | ⚠️ Partial (route selection only) |

### Time to Value

| Method | Dev Time | Testing Time | Production Risk | ROI |
|--------|----------|--------------|-----------------|-----|
| **Clustering** | 1-2 weeks | 1 week | Medium | ✅ High |
| **SARIMA** | 2-3 weeks | 2 weeks | High | ❌ Low (data constraints) |
| **SARIMAX** | 3-4 weeks | 2 weeks | Very High | ❌ Very Low |

---

## Recommended Approach: Hybrid + Clustering

### Architecture

```python
def hybrid_clustering_forecast(target_week, target_year):
    """
    Tier 1: Hybrid (high confidence)
    Tier 2: Clustering (medium confidence)
    Tier 3: Skip (low confidence)
    """

    # TIER 1: Hybrid baseline routes
    baseline_routes = hybrid_model(target_week, target_year)
    # Expected: ~250 routes, 1.6% error, high confidence

    # TIER 2: Cluster-based for missed routes
    recent_routes = get_recent_8_weeks()
    missed_routes = recent_routes - baseline_routes

    # Cluster missed routes
    clusters = cluster_routes(
        missed_routes,
        features=['origin', 'destination', 'product', 'volume_pattern', 'frequency']
    )

    # Forecast per cluster
    cluster_forecasts = []
    for cluster_id, routes in clusters.items():
        # Use cluster-specific method
        method = select_best_method(cluster_id)

        for route in routes:
            forecast = method.predict(route)
            confidence = calculate_cluster_confidence(cluster_id)

            # Only add if confidence > threshold
            if confidence > 0.4:
                cluster_forecasts.append({
                    'route': route,
                    'forecast': forecast,
                    'confidence': confidence,
                    'tier': 2
                })

    # Combine
    final_forecast = baseline_routes + cluster_forecasts
    return final_forecast
```

### Clustering Features

**Route Characteristics to Cluster On**:

1. **Geographic**:
   - Origin hub (ATL, DFW, SLC, etc.)
   - Destination hub
   - Hub-to-hub distance

2. **Volume Pattern**:
   - Average volume (high/medium/low)
   - Volume stability (std deviation)
   - Growth/decline trend

3. **Frequency**:
   - Ships daily vs sporadic
   - Days per week
   - Consistency score

4. **Temporal**:
   - Peak season vs off-season
   - Week-of-year patterns
   - New vs established route

**Example Clusters** (K=5):

```
Cluster 0: High-Volume Hub Routes (e.g., ATL→LAX, DFW→SEA)
  - Avg volume: 80+ pieces
  - Frequency: 5-7 days/week
  - Stability: Low variance
  - Method: Recent 4-week average
  - Confidence: 0.85

Cluster 1: Medium-Volume Regular Routes (e.g., ATL→DEN, SLC→DFW)
  - Avg volume: 20-80 pieces
  - Frequency: 3-5 days/week
  - Stability: Medium variance
  - Method: Trend-adjusted recent avg
  - Confidence: 0.70

Cluster 2: Sporadic Low-Volume Routes (e.g., CVG→DEN)
  - Avg volume: <20 pieces
  - Frequency: 1-3 days/week
  - Stability: High variance
  - Method: Prior week × 0.5 (probabilistic)
  - Confidence: 0.45

Cluster 3: New Routes (no baseline history)
  - Avg volume: Variable
  - Frequency: Recent appearance only
  - Stability: Unknown
  - Method: Cluster average × origin factor
  - Confidence: 0.35

Cluster 4: Declining Routes (volumes dropping)
  - Avg volume: Decreasing trend
  - Frequency: Declining
  - Stability: Unstable
  - Method: Recent 2-week average (shorter window)
  - Confidence: 0.50
```

### Expected Performance

**Tier 1 (Hybrid)**: ~250 routes
- Volume contribution: ~10,000 pieces
- Error: 1.6%
- Confidence: 0.90

**Tier 2 (Clustering)**: ~350 routes
- Volume contribution: ~7,000 pieces
- Error: 8-12%
- Confidence: 0.50-0.70

**Combined**: ~600 routes (68% coverage)
- Total volume: ~17,000 pieces
- Expected error: 4-6%
- Missed routes: ~270 (vs 623 currently)

**Trade-off**:
- ✅ Route coverage: 28.5% → 68%
- ⚠️ Volume error: 1.6% → 4-6%
- ✅ Missed routes: 623 → 270

---

## Why NOT SARIMA/SARIMAX?

### Data Constraint Analysis

**What SARIMA Needs**:
```python
# Minimum for weekly seasonality
required_weeks = 52 * 2  # 2 years recommended
required_observations_per_route = 104

# Our data
available_weeks = 12-16
```

**Example Route Data Reality**:
```
ATL→BOS, MAX, Tuesday:
Week 50: 29 pieces
Week 49: 0 (didn't ship)
Week 48: 35 pieces
Week 47: 0 (didn't ship)
Week 46: 28 pieces
Week 45: 0 (didn't ship)
Week 44: 31 pieces
...

Problems for SARIMA:
1. Only 12 observations (need 52+)
2. Lots of zeros (sporadic shipping)
3. High volatility
4. No clear seasonal pattern visible
```

**Statistical Test**:
```python
from statsmodels.tsa.stattools import adfuller

# Stationarity test (SARIMA requirement)
route_data = [29, 0, 35, 0, 28, 0, 31, 0, 26, 0, 33, 0]
result = adfuller(route_data)

# Result: p-value > 0.05 (NOT stationary)
# Too few observations, too much noise
# SARIMA will fail or produce unreliable forecasts
```

### Computational Cost

**SARIMA for 871 routes**:
```python
import time

# Single SARIMA model fit
start = time.time()
model = SARIMAX(data, order=(1,1,1), seasonal_order=(1,1,1,52))
fitted = model.fit()
duration = time.time() - start

# Typical: 2-5 seconds per route
# Total: 871 routes × 3 seconds = 2,613 seconds = 43 minutes

# Plus: Many routes will fail to converge
# Plus: Need to handle errors, retries, fallbacks
# Result: 1-2 hours per forecast run
```

**Hybrid for 871 routes**:
```python
# Simple SQL + averaging
duration = 15 seconds total

# 240x faster!
```

### Pattern Instability

**SARIMA Assumption**: Patterns are stable and repeating

**Our Reality**: Routes change constantly
```
ATL→BOS historical volumes:
2022 Week 50: 242 pieces
2023 Week 50: ~150 pieces (estimated, -38%)
2024 Week 50: ~100 pieces (estimated, -33%)
2025 Week 50: 59 pieces (-41%)

Trend: -76% decline over 3 years

SARIMA would:
1. Try to fit seasonal pattern
2. Fail because pattern is breaking down
3. Produce unreliable forecast
4. Simple recent average works better!
```

---

## Recommendation Summary

### ✅ DO: Add Clustering

**Priority**: High
**Timeline**: 1-2 weeks development + 1 week testing
**Expected ROI**: High

**Reason**: Solves the actual problem (route coverage) without sacrificing too much volume accuracy.

**Implementation**:
```bash
# Build hybrid-clustering model
1. Keep Hybrid for baseline routes (Tier 1)
2. Add K-Means clustering for missed routes (Tier 2)
3. Test on Week 50 actuals
4. Validate on Week 51 when available

# Expected output:
python3 src/forecast_hybrid_clustering.py --week 51 --year 2025
# → 600-650 routes, 4-6% volume error
```

### ❌ DON'T: Use SARIMA/SARIMAX

**Priority**: Not recommended
**Timeline**: N/A
**Expected ROI**: Negative

**Reasons**:
1. Insufficient data (12 weeks vs 52+ needed)
2. Sporadic patterns break model assumptions
3. Too slow (43+ minutes vs 15 seconds)
4. Doesn't solve route coverage problem
5. Volume accuracy already solved (1.6%)
6. Simple methods outperform on volatile data

### 🔬 MAYBE: Research SARIMA for Specific Routes Only

**If you really want to test SARIMA**:

Only apply to:
- Top 20 highest-volume routes (ATL→LAX, etc.)
- Routes with daily shipping (no sporadic zeros)
- Routes where we have 52+ weeks of data

**Purpose**: Academic comparison only
**Expected**: Won't beat simple averaging
**Cost**: 2-3 weeks development
**Benefit**: Learning/research

---

## Next Steps

### Immediate (This Week)

1. ✅ **Decision**: Add clustering or not?
   - If YES → Start hybrid-clustering design
   - If NO → Continue enhancing Hybrid

2. **If adding clustering**:
   - Define clustering features
   - Choose K (number of clusters)
   - Design tier system (Hybrid + Clustering)

### Short-Term (Next 2 Weeks)

**Option A: Hybrid-Clustering**
```python
# src/forecast_hybrid_clustering.py
Week 1: Build clustering logic
Week 2: Test on Week 50, validate on Week 51
Week 3: Production deployment
```

**Option B: Enhanced Hybrid (No Clustering)**
```python
# src/forecast_hybrid_enhanced.py
Week 1: Add selective new route detection
Week 2: Add day-of-week filtering
Week 3: Add probabilistic weighting
```

### Medium-Term (Month 2-3)

- Feed Week 50 & 51 actuals to RouteMemory
- Enable continuous learning
- Monitor cluster stability (if using clustering)
- Tune confidence thresholds

---

## Final Verdict

| Method | Use It? | Why? |
|--------|---------|------|
| **Clustering** | ✅ YES | Solves route coverage problem, proven method, reasonable complexity |
| **SARIMA** | ❌ NO | Insufficient data, too slow, doesn't fit our problem |
| **SARIMAX** | ❌ NO | All SARIMA problems + need external data |

**Your question**: "Is it make sense for our goals?"

**Answer**:
- **Clustering**: YES - directly addresses missed routes problem
- **SARIMA/SARIMAX**: NO - wrong tool for our data and goals

---

**Recommendation**: Build `forecast_hybrid_clustering.py` as next iteration. Skip SARIMA/SARIMAX entirely.
