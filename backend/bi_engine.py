"""
NexusAI - Enterprise Business Intelligence, Customer Analytics & Forecasting Engine
Implements high-performance Python analytics for:
1. Financial & Operational Summary KPIs
2. Monthly & Daily Revenue/Profit Trends
3. Time-Series Forecasting (Holt-Winters Exponential Smoothing & Linear Trend)
4. Customer RFM Segmentation & Behavior Intelligence
5. Product & Geographic Affinity Cross-Tabulation
6. Automated Executive Strategic Narrative
"""

import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger("nexus.bi")


class NexusBIEngine:
    def __init__(self, df: pd.DataFrame, mapping: Dict[str, str]):
        self.raw_df = df.copy()
        self.mapping = {k: v for k, v in mapping.items() if v and v in df.columns}
        self.df = self._clean_and_prepare_data()

    def _clean_and_prepare_data(self) -> pd.DataFrame:
        df = self.raw_df.copy()

        # Helper to safely clean numeric columns
        def clean_num(col_series):
            if pd.api.types.is_numeric_dtype(col_series):
                return pd.to_numeric(col_series, errors="coerce")
            # Strip $, commas, spaces, %
            cleaned = col_series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
            return pd.to_numeric(cleaned, errors="coerce")

        numeric_fields = ["sales", "profit", "quantity", "price", "discount", "tax", "shipping_cost"]
        for field in numeric_fields:
            if field in self.mapping:
                col = self.mapping[field]
                df[col] = clean_num(df[col])

        # Date parsing
        if "date" in self.mapping:
            date_col = self.mapping["date"]
            try:
                df["__parsed_date"] = pd.to_datetime(df[date_col], errors="coerce")
            except Exception as e:
                logger.warning(f"Error parsing date column: {e}")
                df["__parsed_date"] = pd.NaT
        else:
            df["__parsed_date"] = pd.NaT

        return df

    def compute_all_analytics(self) -> Dict[str, Any]:
        """Runs the entire BI suite and returns structured data ready for interactive charts."""
        summary = self.compute_summary_kpis()
        trends = self.compute_revenue_trends()
        forecast = self.compute_forecast(periods=6)
        customer_intel = self.compute_customer_intelligence()
        product_affinity = self.compute_product_affinity()
        geo_breakdown = self.compute_geographic_breakdown()
        executive_narrative = self.generate_executive_narrative(summary, trends, customer_intel)

        return {
            "summary_kpis": summary,
            "trends": trends,
            "forecast": forecast,
            "customer_intelligence": customer_intel,
            "product_affinity": product_affinity,
            "geographic_breakdown": geo_breakdown,
            "executive_narrative": executive_narrative,
            "mapping_used": self.mapping
        }

    def compute_summary_kpis(self) -> Dict[str, Any]:
        df = self.df
        total_rows = len(df)
        sales_col = self.mapping.get("sales")
        profit_col = self.mapping.get("profit")
        qty_col = self.mapping.get("quantity")
        cust_col = self.mapping.get("customer_id") or self.mapping.get("customer_name")
        prod_col = self.mapping.get("product_name") or self.mapping.get("product_id")
        disc_col = self.mapping.get("discount")

        total_sales = float(df[sales_col].sum()) if sales_col and sales_col in df.columns else 0.0
        total_profit = float(df[profit_col].sum()) if profit_col and profit_col in df.columns else 0.0
        total_qty = int(df[qty_col].sum()) if qty_col and qty_col in df.columns else total_rows
        avg_sale = float(df[sales_col].mean()) if sales_col and sales_col in df.columns else 0.0
        unique_customers = int(df[cust_col].nunique()) if cust_col and cust_col in df.columns else 0
        unique_products = int(df[prod_col].nunique()) if prod_col and prod_col in df.columns else 0
        
        profit_margin = round((total_profit / total_sales) * 100, 2) if total_sales > 0 else 0.0
        avg_discount = round(float(df[disc_col].mean()), 2) if disc_col and disc_col in df.columns else 0.0

        return {
            "total_revenue": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin_pct": profit_margin,
            "total_orders": total_rows,
            "total_units_sold": total_qty,
            "average_order_value": round(avg_sale, 2),
            "unique_customers": unique_customers,
            "unique_products": unique_products,
            "average_discount_pct": avg_discount
        }

    def compute_revenue_trends(self) -> Dict[str, Any]:
        df = self.df
        sales_col = self.mapping.get("sales")
        profit_col = self.mapping.get("profit")

        if "__parsed_date" not in df.columns or df["__parsed_date"].isna().all() or not sales_col:
            # Fallback to row index if no date available
            return {
                "has_dates": False,
                "labels": [f"T-{i}" for i in range(1, min(len(df), 20) + 1)],
                "revenue": [round(float(x), 2) for x in df[sales_col].head(20).fillna(0)] if sales_col else [],
                "profit": [round(float(x), 2) for x in df[profit_col].head(20).fillna(0)] if profit_col else []
            }

        valid_dates_df = df.dropna(subset=["__parsed_date"]).copy()
        valid_dates_df.sort_values(by="__parsed_date", inplace=True)
        
        # Monthly aggregation
        valid_dates_df["month_period"] = valid_dates_df["__parsed_date"].dt.to_period("M").astype(str)
        monthly = valid_dates_df.groupby("month_period").agg({
            sales_col: "sum",
            **( {profit_col: "sum"} if profit_col else {} )
        }).reset_index()

        labels = monthly["month_period"].tolist()
        revenue = [round(float(x), 2) for x in monthly[sales_col].tolist()]
        profit = [round(float(x), 2) for x in monthly[profit_col].tolist()] if profit_col else []

        # Month-over-month growth rates
        growth_rates = []
        for i in range(len(revenue)):
            if i == 0 or revenue[i - 1] == 0:
                growth_rates.append(0.0)
            else:
                growth = round(((revenue[i] - revenue[i - 1]) / revenue[i - 1]) * 100, 2)
                growth_rates.append(growth)

        return {
            "has_dates": True,
            "labels": labels,
            "revenue": revenue,
            "profit": profit,
            "mom_growth": growth_rates,
            "latest_growth_pct": growth_rates[-1] if growth_rates else 0.0
        }

    def compute_forecast(self, target_metric: str = "sales", periods: int = 6) -> Dict[str, Any]:
        """Calculates multi-period time-series projections with confidence bands."""
        if not isinstance(periods, int) or periods < 1 or periods > 24:
            return {"status": "error", "message": "Forecast periods must be between 1 and 24."}
        df = self.df
        col = self.mapping.get(target_metric)
        if not col or col not in df.columns:
            return {"status": "error", "message": f"Target metric '{target_metric}' not available."}

        series_data = []
        date_labels = []

        if "__parsed_date" in df.columns and not df["__parsed_date"].isna().all():
            vdf = df.dropna(subset=["__parsed_date"]).copy()
            vdf["period"] = vdf["__parsed_date"].dt.to_period("M").astype(str)
            agg = vdf.groupby("period")[col].sum().reset_index()
            date_labels = agg["period"].tolist()
            series_data = agg[col].tolist()
        else:
            series_data = df[col].dropna().head(30).tolist()
            date_labels = [f"Step-{i+1}" for i in range(len(series_data))]

        if len(series_data) < 3:
            return {"status": "error", "message": "Insufficient data points for forecasting."}

        y = np.asarray(series_data, dtype=float)
        y = y[np.isfinite(y)]
        if len(y) < 3:
            return {"status": "error", "message": "Insufficient finite data points for forecasting."}
        n = len(y)
        forecast_values = []
        lower_bounds = []
        upper_bounds = []
        method = "Exponential Smoothing (Holt-Winters)"

        # Try Statsmodels Exponential Smoothing
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            trend_type = "add" if n >= 5 else None
            model = ExponentialSmoothing(y, trend=trend_type, seasonal=None, initialization_method="estimated")
            fit = model.fit()
            pred = fit.forecast(periods)
            forecast_values = [round(float(x), 2) for x in pred]

            # Approximate confidence intervals from residuals
            residuals = y - fit.fittedvalues
            std_err = float(np.std(residuals)) if len(residuals) > 0 else float(np.std(y) * 0.1)
            for i, val in enumerate(forecast_values):
                spread = std_err * (1.2 + (i * 0.2))
                lower_bounds.append(round(max(0, val - 1.96 * spread), 2))
                upper_bounds.append(round(val + 1.96 * spread, 2))
        except Exception as e:
            logger.info(f"Exponential smoothing fallback: {e}")
            method = "Linear Trend Extrapolation"
            x = np.arange(n)
            poly = np.polyfit(x, y, 1)
            future_x = np.arange(n, n + periods)
            preds = np.polyval(poly, future_x)
            forecast_values = [round(float(max(0, val)), 2) for val in preds]
            std_err = float(np.std(y) * 0.15)
            for i, val in enumerate(forecast_values):
                spread = std_err * (1.0 + (i * 0.15))
                lower_bounds.append(round(max(0, val - 1.96 * spread), 2))
                upper_bounds.append(round(val + 1.96 * spread, 2))

        # Generate future labels
        if date_labels and "-" in date_labels[-1]:
            last_period = date_labels[-1]
            try:
                dt = datetime.strptime(last_period, "%Y-%m")
                future_labels = []
                for p in range(1, periods + 1):
                    # add p months
                    m = (dt.month + p - 1) % 12 + 1
                    y_offset = (dt.month + p - 1) // 12
                    f_dt = datetime(dt.year + y_offset, m, 1)
                    future_labels.append(f_dt.strftime("%Y-%m"))
            except Exception:
                future_labels = [f"Period +{i+1}" for i in range(periods)]
        else:
            future_labels = [f"Step +{i+1}" for i in range(periods)]

        avg_history = float(np.mean(y[-3:])) if len(y) >= 3 else float(np.mean(y))
        avg_forecast = float(np.mean(forecast_values))
        projected_growth = round(((avg_forecast - avg_history) / avg_history) * 100, 2) if avg_history > 0 else 0.0

        return {
            "status": "ok",
            "method": method,
            "target": target_metric,
            "periods": periods,
            "history_labels": date_labels,
            "history_values": [round(float(v), 2) for v in y],
            "forecast_labels": future_labels,
            "forecast_values": forecast_values,
            "lower_bounds": lower_bounds,
            "upper_bounds": upper_bounds,
            "projected_growth_pct": projected_growth
        }

    def compute_customer_intelligence(self) -> Dict[str, Any]:
        """Calculates RFM (Recency, Frequency, Monetary) segmentation and concentration metrics."""
        df = self.df
        cust_col = self.mapping.get("customer_id") or self.mapping.get("customer_name")
        sales_col = self.mapping.get("sales")

        if not cust_col or cust_col not in df.columns or not sales_col:
            return {"available": False}

        # Determine reference date
        if "__parsed_date" in df.columns and not df["__parsed_date"].isna().all():
            max_date = df["__parsed_date"].max()
            rfm = df.groupby(cust_col).agg({
                "__parsed_date": lambda x: (max_date - x.max()).days,
                sales_col: ["count", "sum"]
            })
            rfm.columns = ["recency_days", "frequency", "monetary"]
        else:
            rfm = df.groupby(cust_col).agg({
                sales_col: ["count", "sum"]
            })
            rfm.columns = ["frequency", "monetary"]
            # Without dates, recency is unknown; use a neutral, deterministic score.
            rfm["recency_days"] = 0

        rfm = rfm.reset_index()

        # Score quintiles
        try:
            rfm["r_score"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop")
        except Exception:
            rfm["r_score"] = 3

        try:
            rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
        except Exception:
            rfm["f_score"] = 3

        try:
            rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
        except Exception:
            rfm["m_score"] = 3

        rfm["r_score"] = pd.to_numeric(rfm["r_score"], errors="coerce").fillna(3).astype(int)
        rfm["f_score"] = pd.to_numeric(rfm["f_score"], errors="coerce").fillna(3).astype(int)
        rfm["m_score"] = pd.to_numeric(rfm["m_score"], errors="coerce").fillna(3).astype(int)

        # Categorize into Actionable Personas
        def assign_segment(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 4 and f >= 4 and m >= 4:
                return "Champions"
            elif r >= 3 and f >= 3:
                return "Loyal Customers"
            elif r >= 4 and f <= 2:
                return "Potential Loyalists"
            elif r >= 3 and f == 1:
                return "Promising / Recent"
            elif r <= 2 and (f >= 3 or m >= 3):
                return "At Risk"
            else:
                return "Hibernating / Lost"

        rfm["segment"] = rfm.apply(assign_segment, axis=1)

        # Segment breakdown
        segment_counts = rfm["segment"].value_counts().to_dict()
        segment_revenue = rfm.groupby("segment")["monetary"].sum().round(2).to_dict()

        # Customer concentration (Pareto principle)
        sorted_m = rfm.sort_values(by="monetary", ascending=False)["monetary"]
        top_10_pct_count = max(1, int(len(sorted_m) * 0.10))
        top_10_revenue = sorted_m.head(top_10_pct_count).sum()
        total_rev = sorted_m.sum()
        top_10_share_pct = round((top_10_revenue / total_rev) * 100, 2) if total_rev > 0 else 0.0

        repeat_customers = int((rfm["frequency"] > 1).sum())
        repeat_rate_pct = round((repeat_customers / len(rfm)) * 100, 2) if len(rfm) > 0 else 0.0

        return {
            "available": True,
            "total_tracked_customers": len(rfm),
            "repeat_customers_count": repeat_customers,
            "repeat_rate_pct": repeat_rate_pct,
            "top_10_pct_revenue_share": top_10_share_pct,
            "segments": {
                name: {
                    "count": int(segment_counts.get(name, 0)),
                    "total_revenue": float(segment_revenue.get(name, 0.0)),
                    "pct_of_customers": round((int(segment_counts.get(name, 0)) / len(rfm)) * 100, 1)
                }
                for name in ["Champions", "Loyal Customers", "Potential Loyalists", "Promising / Recent", "At Risk", "Hibernating / Lost"]
            },
            "top_customers": [
                {
                    "customer": str(row[cust_col]),
                    "orders": int(row["frequency"]),
                    "total_spent": round(float(row["monetary"]), 2),
                    "segment": str(row["segment"])
                }
                for _, row in rfm.sort_values(by="monetary", ascending=False).head(8).iterrows()
            ]
        }

    def compute_product_affinity(self) -> Dict[str, Any]:
        """Calculates top products, high-margin drivers, and category performance."""
        df = self.df
        prod_col = self.mapping.get("product_name") or self.mapping.get("product_id")
        cat_col = self.mapping.get("category")
        sales_col = self.mapping.get("sales")
        profit_col = self.mapping.get("profit")
        qty_col = self.mapping.get("quantity")

        if not sales_col or sales_col not in df.columns:
            return {"available": False}

        results: Dict[str, Any] = {"available": True}

        # Top products by revenue
        if prod_col and prod_col in df.columns:
            prod_agg = df.groupby(prod_col).agg({
                sales_col: "sum",
                **( {profit_col: "sum"} if profit_col else {} ),
                **( {qty_col: "sum"} if qty_col else {} )
            }).reset_index()

            top_rev = prod_agg.sort_values(by=sales_col, ascending=False).head(10)
            results["top_products_revenue"] = {
                "labels": top_rev[prod_col].astype(str).tolist(),
                "values": [round(float(v), 2) for v in top_rev[sales_col].tolist()]
            }

            if profit_col:
                top_margin = prod_agg[prod_agg[sales_col] > 0].copy()
                top_margin["margin_pct"] = (top_margin[profit_col] / top_margin[sales_col]) * 100
                top_margin = top_margin.sort_values(by="margin_pct", ascending=False).head(8)
                results["top_products_margin"] = {
                    "labels": top_margin[prod_col].astype(str).tolist(),
                    "values": [round(float(v), 1) for v in top_margin["margin_pct"].tolist()]
                }

        # Category Breakdown
        if cat_col and cat_col in df.columns:
            cat_agg = df.groupby(cat_col).agg({
                sales_col: "sum",
                **( {profit_col: "sum"} if profit_col else {} )
            }).reset_index().sort_values(by=sales_col, ascending=False)

            results["categories"] = {
                "labels": cat_agg[cat_col].astype(str).tolist(),
                "sales": [round(float(v), 2) for v in cat_agg[sales_col].tolist()],
                "profit": [round(float(v), 2) for v in cat_agg[profit_col].tolist()] if profit_col else []
            }

        return results

    def compute_geographic_breakdown(self) -> Dict[str, Any]:
        """Calculates regional distribution and cross-category market affinities."""
        df = self.df
        region_col = self.mapping.get("region") or self.mapping.get("country") or self.mapping.get("city")
        cat_col = self.mapping.get("category")
        sales_col = self.mapping.get("sales")

        if not region_col or region_col not in df.columns or not sales_col:
            return {"available": False}

        reg_agg = df.groupby(region_col)[sales_col].sum().reset_index()
        reg_agg = reg_agg.sort_values(by=sales_col, ascending=False).head(8)

        # Region x Category cross-tab if both exist
        crosstab_data = {}
        if cat_col and cat_col in df.columns:
            ct = pd.crosstab(df[region_col], df[cat_col], values=df[sales_col], aggfunc="sum").fillna(0)
            crosstab_data = {
                "regions": ct.index.astype(str).tolist()[:6],
                "categories": ct.columns.astype(str).tolist()[:5],
                "matrix": ct.iloc[:6, :5].round(2).values.tolist()
            }

        return {
            "available": True,
            "labels": reg_agg[region_col].astype(str).tolist(),
            "values": [round(float(v), 2) for v in reg_agg[sales_col].tolist()],
            "crosstab": crosstab_data
        }

    def generate_executive_narrative(self, summary: Dict[str, Any], trends: Dict[str, Any], customer_intel: Dict[str, Any]) -> str:
        """Synthesizes high-level executive strategic takeaways from calculated metrics."""
        rev = summary.get("total_revenue", 0)
        margin = summary.get("profit_margin_pct", 0)
        orders = summary.get("total_orders", 0)
        aov = summary.get("average_order_value", 0)

        lines = [
            f"Business Performance Summary: Enterprise generated ${rev:,.2f} across {orders:,} transactions with an Average Order Value (AOV) of ${aov:,.2f}.",
            f"Profitability Profile: Operating at an overall net profit margin of {margin}%.",
        ]

        if customer_intel.get("available"):
            rep_rate = customer_intel.get("repeat_rate_pct", 0)
            top_share = customer_intel.get("top_10_pct_revenue_share", 0)
            lines.append(f"Customer Loyalty Dynamics: Strong customer retention with a {rep_rate}% repeat purchase rate. Top 10% of customers account for {top_share}% of total corporate revenue (Pareto distribution).")

        if trends.get("has_dates") and trends.get("mom_growth"):
            latest_g = trends.get("latest_growth_pct", 0)
            trend_dir = "expansion" if latest_g >= 0 else "contraction"
            lines.append(f"Growth Velocity: Latest month registered a {abs(latest_g)}% {trend_dir} in top-line transaction volume.")

        return " ".join(lines)
