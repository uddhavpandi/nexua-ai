"""
NexusAI - TypeSafe Jev Column & Schema Understanding Engine
Uses TypeSafe AI Jev (System One classification model) to quickly and deterministically
understand table schema, map raw column names to BI standard dimensions/metrics,
and infer company domain & context.
Includes intelligent semantic fallback for offline/development execution.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("nexus.jev")

STANDARD_FIELDS = [
    "sales", "profit", "quantity", "price", "discount", "tax", "shipping_cost",
    "date", "customer_id", "customer_name", "customer_segment",
    "product_id", "product_name", "category", "subcategory",
    "region", "city", "country", "payment_method", "other"
]

# Comprehensive alias patterns for heuristic / fallback matching
FALLBACK_ALIASES = {
    "date": [
        "date", "order_date", "orderdate", "trans_date", "transaction_date",
        "invoice_date", "purchase_date", "sale_date", "ship_date", "created_at",
        "timestamp", "period", "month", "time"
    ],
    "sales": [
        "sales", "revenue", "total_revenue", "amount", "total_sales", "sale_amount",
        "net_sales", "gross_sales", "total_amount", "grand_total", "turnover", "value"
    ],
    "profit": [
        "profit", "net_profit", "gross_profit", "margin", "earnings", "net_margin"
    ],
    "quantity": [
        "quantity", "qty", "units", "units_sold", "volume", "order_qty", "count"
    ],
    "price": [
        "price", "unit_price", "mrp", "cost_price", "sale_price", "rate"
    ],
    "discount": [
        "discount", "discount_pct", "discount_percent", "discount_amount", "promo_disc", "rebate"
    ],
    "shipping_cost": [
        "shipping_cost", "freight", "shipping", "delivery_fee", "transport_cost"
    ],
    "tax": [
        "tax", "vat", "gst", "sales_tax", "duty", "tariff"
    ],
    "customer_id": [
        "customer_id", "cust_id", "client_id", "buyer_id", "user_id", "account_id"
    ],
    "customer_name": [
        "customer_name", "customer", "client_name", "client", "buyer_name", "buyer"
    ],
    "customer_segment": [
        "customer_segment", "segment", "tier", "customer_type", "client_tier"
    ],
    "product_id": [
        "product_id", "prod_id", "sku", "item_id", "item_code", "article_number"
    ],
    "product_name": [
        "product_name", "product", "item_name", "item", "title", "description", "goods"
    ],
    "category": [
        "category", "product_category", "department", "division", "class", "genre"
    ],
    "subcategory": [
        "subcategory", "sub_category", "sub_dept", "subclass"
    ],
    "region": [
        "region", "zone", "territory", "area", "market", "continent"
    ],
    "city": [
        "city", "town", "metro", "municipality"
    ],
    "country": [
        "country", "nation", "state", "province"
    ],
    "payment_method": [
        "payment_method", "payment_type", "pay_mode", "tender_type", "gateway"
    ]
}


def normalize_string(val: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(val).strip().lower())


class JevColumnDetector:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TYPESAFE_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from typesafe_sdk import TypeSafeClient
                self.client = TypeSafeClient(api_key=self.api_key)
                logger.info("TypeSafe Jev SDK initialized successfully with API key.")
            except Exception as e:
                logger.warning(f"Could not initialize TypeSafeClient: {e}. Will use intelligent semantic fallback.")

    def classify_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Inspects each column in the table, determines its business role using Jev
        (or semantic fallback), and extracts company context.
        """
        detected_mapping: Dict[str, str] = {}
        column_meta: Dict[str, Dict[str, Any]] = {}
        used_cols = set()

        # Step 1: Analyze each raw column individually
        for col_name in df.columns:
            series = df[col_name]
            meta = self._analyze_single_column(col_name, series)
            column_meta[col_name] = meta

        # Step 2: Optimal assignment of standard fields to best-matching raw columns
        # Sort candidates by confidence score
        role_candidates: Dict[str, List[tuple]] = {f: [] for f in STANDARD_FIELDS if f != "other"}
        for col_name, meta in column_meta.items():
            role = meta["predicted_role"]
            conf = meta["confidence"]
            if role in role_candidates:
                role_candidates[role].append((conf, col_name))

        # Assign standard roles to highest-confidence column first
        for role, candidates in role_candidates.items():
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                # Pick the best that hasn't been claimed yet
                for conf, col_name in candidates:
                    if col_name not in used_cols and conf >= 0.50:
                        detected_mapping[role] = col_name
                        used_cols.add(col_name)
                        break

        # Step 3: Infer Company Profile & Business Domain from context
        company_profile = self._infer_company_profile(df, detected_mapping)

        return {
            "detected_mapping": detected_mapping,
            "column_meta": column_meta,
            "company_profile": company_profile,
            "jev_enabled": bool(self.client is not None),
        }

    def _analyze_single_column(self, col_name: str, series: pd.Series) -> Dict[str, Any]:
        """Analyzes a column using TypeSafe Jev if available, else semantic heuristics."""
        clean_name = normalize_string(col_name)
        non_null = series.dropna()
        sample_vals = non_null.head(5).astype(str).tolist()
        num_unique = int(non_null.nunique())
        dtype_str = str(series.dtype)

        # Try TypeSafe Jev first if client exists
        if self.client:
            try:
                state_text = (
                    f"Column Name: '{col_name}'\n"
                    f"Data Type: {dtype_str}\n"
                    f"Sample Values: {sample_vals}\n"
                    f"Unique Count: {num_unique} out of {len(series)} total rows\n"
                )
                questions = {
                    "role": {
                        "type": "choice",
                        "instructions": "Classify this column into the most accurate business intelligence field.",
                        "options": STANDARD_FIELDS
                    },
                    "confidence": {
                        "type": "score",
                        "instructions": "Rate confidence in this classification from 0.0 to 1.0."
                    }
                }
                res = self.client.system_one(
                    model="jev-latest",
                    state=state_text,
                    questions=questions
                )
                pred_role = str(res.answers["role"].choice)
                conf = float(res.answers["confidence"].score)
                return {
                    "raw_name": col_name,
                    "predicted_role": pred_role,
                    "confidence": round(conf, 2),
                    "source": "TypeSafe Jev (System One)",
                    "samples": sample_vals
                }
            except Exception as e:
                logger.debug(f"Jev call failed for {col_name}: {e}. Falling back to semantic engine.")

        # Fallback: Multi-factor Semantic & Statistical Classifier
        return self._semantic_fallback(col_name, clean_name, series, sample_vals, num_unique)

    def _semantic_fallback(self, col_name: str, clean_name: str, series: pd.Series,
                           sample_vals: List[str], num_unique: int) -> Dict[str, Any]:
        best_role = "other"
        best_score = 0.0

        # Check alias dictionaries
        for field, aliases in FALLBACK_ALIASES.items():
            for alias in aliases:
                norm_alias = normalize_string(alias)
                if clean_name == norm_alias:
                    score = 0.96
                elif clean_name.startswith(norm_alias) or clean_name.endswith(norm_alias):
                    score = 0.85
                elif norm_alias in clean_name:
                    score = 0.72
                else:
                    continue

                if score > best_score:
                    best_score = score
                    best_role = field

        # Content validation boost / penalty
        is_num = pd.api.types.is_numeric_dtype(series)

        # Date validation check
        if best_role == "date" or "date" in clean_name or "time" in clean_name:
            try:
                pd.to_datetime(sample_vals[:3], errors="raise")
                best_role = "date"
                best_score = max(best_score, 0.95)
            except Exception:
                pass

        # If detected as numeric metric, verify it's actually numeric or cleanable
        if best_role in ["sales", "profit", "price", "quantity", "discount", "tax", "shipping_cost"]:
            if is_num:
                best_score = min(best_score + 0.1, 0.99)
            else:
                # Check if strings are formatted currency (e.g. '$1,200.50')
                clean_nums = [re.sub(r"[^0-9.\-]", "", s) for s in sample_vals]
                can_convert = all(bool(s) for s in clean_nums)
                if can_convert:
                    best_score = min(best_score + 0.05, 0.92)
                else:
                    best_score *= 0.5  # Penalize non-numeric strings

        # Distinguish customer_id vs customer_name
        if "customer" in clean_name or "cust" in clean_name or "client" in clean_name:
            if "id" in clean_name or "code" in clean_name or "no" in clean_name:
                best_role = "customer_id"
                best_score = 0.95
            elif "name" in clean_name:
                best_role = "customer_name"
                best_score = 0.95

        # Distinguish product_id vs product_name
        if "product" in clean_name or "item" in clean_name or "sku" in clean_name:
            if "id" in clean_name or "sku" in clean_name or "code" in clean_name:
                best_role = "product_id"
                best_score = 0.95
            elif "name" in clean_name or "title" in clean_name or clean_name in ["product", "item"]:
                best_role = "product_name"
                best_score = 0.95

        return {
            "raw_name": col_name,
            "predicted_role": best_role if best_score >= 0.5 else "other",
            "confidence": round(best_score if best_score >= 0.5 else 0.3, 2),
            "source": "Nexus Semantic Engine",
            "samples": sample_vals
        }

    def _infer_company_profile(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Deduces the business domain and industry profile from product, category, and data patterns."""
        category_col = mapping.get("category")
        product_col = mapping.get("product_name")

        sample_categories = []
        sample_products = []

        if category_col and category_col in df.columns:
            sample_categories = [str(x) for x in df[category_col].dropna().unique()[:8]]

        if product_col and product_col in df.columns:
            sample_products = [str(x) for x in df[product_col].dropna().unique()[:8]]

        combined_text = " ".join(sample_categories + sample_products).lower()

        # Domain keywords mapping
        if any(w in combined_text for w in ["laptop", "monitor", "headphone", "usb", "keyboard", "watch", "tech", "gadget", "phone"]):
            industry = "Consumer Electronics & Tech Hardware"
            news_tags = ["Electronics Supply Chain", "Semiconductor Tariffs", "Consumer Tech Spending", "Holiday Hardware Sales"]
        elif any(w in combined_text for w in ["apparel", "shoe", "shirt", "jacket", "hoodie", "dress", "fashion", "garment"]):
            industry = "Fashion, Apparel & Lifestyle"
            news_tags = ["Cotton & Textile Tariffs", "Retail Foot Traffic", "Holiday Fashion Demand", "Freight Container Rates"]
        elif any(w in combined_text for w in ["chair", "desk", "furniture", "table", "decor", "home", "cabinet"]):
            industry = "Furniture & Office Equipment"
            news_tags = ["Timber & Steel Tariffs", "Commercial Real Estate", "Hybrid Work Demand", "Freight Logistics Costs"]
        elif any(w in combined_text for w in ["food", "beverage", "grocery", "snack", "drink", "coffee", "organic"]):
            industry = "Food & Fast-Moving Consumer Goods (FMCG)"
            news_tags = ["Agricultural Commodities", "Cold Chain Logistics", "Food Inflation", "Festive Food Spending"]
        elif any(w in combined_text for w in ["industrial", "printer", "label", "pallet", "box", "packaging", "hardware", "tool"]):
            industry = "Industrial Supplies, Logistics & Packaging"
            news_tags = ["Manufacturing Index", "Corrugated Paper Costs", "Freight & Trucking", "Industrial Trade Duties"]
        else:
            industry = "Global Omnichannel Commerce & Retail"
            news_tags = ["Consumer Spending Index", "Import Tariffs", "Supply Chain Freight", "Festive Peak Demand"]

        # Geographical footprint
        region_col = mapping.get("region")
        regions = []
        if region_col and region_col in df.columns:
            regions = [str(r) for r in df[region_col].dropna().unique()[:5]]

        return {
            "industry": industry,
            "primary_categories": sample_categories[:6],
            "operating_regions": regions if regions else ["Global / Domestic"],
            "suggested_news_topics": news_tags
        }
