# NexusAI — Autonomous AI Business Intelligence & Real-Time Market Decision Platform

**NexusAI** is an all-in-one autonomous enterprise platform that transforms raw business datasets (CSV / Excel) into automated multidimensional BI analytics, customer behavioral segmentation, machine learning forecasts, and real-time market news decision automation.

---

## ⚡ Core Capabilities

### 1. Autonomous Table & Schema Understanding (TypeSafe Jev AI + Dual Mode)
- **TypeSafe AI Jev (System One classification)**: Leverages non-autoregressive sub-second model intelligence to classify tabular schemas without prompt drift.
- **Intelligent Dual-Mode Fallback**: Evaluates string aliases, cardinalities, date formats, and numeric distributions automatically when running offline or without an API key.
- **Company & Market Profiling**: Automatically infers industry domain (e.g., *Consumer Electronics*, *Fashion & Apparel*, *Industrial Supplies*, *Omnichannel Retail*) from sample product and category distributions.

### 2. Multi-Dimensional Business Intelligence & Customer Analytics
- **Financial & Operational KPIs**: Total Revenue, Net Profit, Profit Margin %, Average Order Value (AOV), Total Orders, Units Sold, and Discount Concession impact.
- **Interactive Time-Series Trends**: Monthly and daily revenue & profit velocity with Month-over-Month (MoM) growth calculations.
- **Customer Behavioral Intelligence (RFM)**:
  - Recency, Frequency, and Monetary scoring across customer bases.
  - Actionable segmentation cohorts: *Champions*, *Loyal Customers*, *Potential Loyalists*, *Promising*, *At Risk*, and *Hibernating*.
  - Customer value concentration (Pareto 80/20 decile share) and repeat purchase rates.
- **Product & Geographic Affinity**:
  - Top 10 products by revenue and highest margin drivers.
  - Cross-regional market affinity matrix (Region $\times$ Category).

### 3. Predictive Multi-Period AI Forecasting
- **Time-Series Projection**: Powered by Holt-Winters Exponential Smoothing (`statsmodels`) and linear trend extrapolation.
- **Confidence Bounds**: Calculates 95% upper and lower confidence intervals.
- **Interactive Metric & Horizon Controls**: Predicts Revenue, Profit, Units, or Price over 3, 6, 12, or 24 periods ahead.

### 4. Live News & Macroeconomic AI Decision Engine
- **Continuous Market Tracking**: Ingests real-time financial, business, and industry news wire updates.
- **Automated Decision Matrix**: Categorizes market events across 4 strategic corporate vectors:
  1. 🚢 **Production, Freight & Supply Chain** (Container spot rates, port congestion, fuel prices)
  2. ⚖️ **Taxes, Tariffs & Trade Regulations** (Customs duties, import taxes, regulatory quotas)
  3. 🎁 **Festive, Seasonal & Peak Demand** (Holiday retail spending, consumer confidence, promotional waves)
  4. 🌪️ **Localized Crises & Regional Shocks** (Weather anomalies, logistics strikes, local market disruptions)
- **Proactive Leadership Directives**: Outputs concrete operational directives (e.g., *"Buffer safety stock by 15-20% for top categories"*, *"Advance seasonal promotional calendar by 3 weeks"*).

### 5. Modern Interactive Dashboard (Chart.js + Glassmorphism)
- Sleek dark-mode aesthetic with custom glowing gradients and backdrop blur.
- Fully interactive canvas charts with hover tooltips, zoom, and live tabbed navigation.
- 1-Click test button to load a realistic pre-bundled Kaggle-style e-commerce dataset with 2,500 transactions.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pandas, NumPy, Scikit-Learn, Statsmodels, HTTPX, Feedparser
- **AI Classification**: `typesafe-sdk` (TypeSafe AI Jev) + Nexus Semantic Engine
- **News Ingestion**: Google News Live RSS Wire + Feedparser + Async HTTPX
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Glassmorphic Design System), Modern JavaScript (ES6+), Chart.js 4.4

---

## 🚀 Quick Start Guide

### 1. Set Up Virtual Environment & Dependencies
```bash
# Clone or navigate to the repository
cd "final nex project"

# Create virtual environment with Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install required packages
pip install -r backend/requirements.txt
```

### 2. (Optional) Set TypeSafe Jev API Key
```bash
export TYPESAFE_API_KEY="ts_live_your_key_here"
```
*(Note: If no key is set, the system automatically runs the built-in intelligent semantic classifier with 100% functionality).*

### 3. Launch the Server
```bash
PYTHONPATH=. .venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open in Browser
Open your browser and navigate to:
```
http://localhost:8000/
```

Click **"✨ Load Sample E-Commerce (2.5k Rows)"** for an immediate 1-click test, or drag and drop your own dataset!
