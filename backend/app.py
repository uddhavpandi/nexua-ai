"""
NexusAI - Enterprise AI Business Intelligence & Real-Time Market Decision Platform
FastAPI Application Server
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.jev_detector import JevColumnDetector
from backend.bi_engine import NexusBIEngine
from backend.news_engine import NewsDecisionEngine
from backend.sample_data import generate_sample_dataset

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Generate sample dataset if not present
SAMPLE_FILE = DATA_DIR / "sample_ecommerce.csv"
generate_sample_dataset(SAMPLE_FILE)

app = FastAPI(
    title="NexusAI Engine API",
    description="Automated AI Business Intelligence, Customer Analytics, and Real-Time Market News Decision Automation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active datasets and profiles
DATASET_CACHE: Dict[str, pd.DataFrame] = {}
PROFILE_CACHE: Dict[str, Dict[str, Any]] = {}
news_engine = NewsDecisionEngine()


def read_uploaded_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    raise HTTPException(status_code=400, detail=f"Unsupported format: {suffix}. Upload CSV or Excel.")


@app.get("/api/health")
def health():
    jev_key = bool(os.getenv("TYPESAFE_API_KEY"))
    return {
        "status": "online",
        "system": "NexusAI Intelligence Engine v2.0",
        "typesafe_jev_connected": jev_key,
        "sample_dataset_ready": SAMPLE_FILE.exists()
    }


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    typesafe_key: Optional[str] = Form(None)
):
    """
    Saves the user dataset, classifies columns with TypeSafe Jev (or semantic fallback),
    infers the company industry profile, and returns a preview.
    """
    suffix = Path(file.filename or "data.csv").suffix.lower()
    if suffix not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(400, "Supported formats: .csv, .xlsx, .xls")

    file_id = uuid.uuid4().hex[:12]
    saved_path = UPLOAD_DIR / f"{file_id}{suffix}"

    with open(saved_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        df = read_uploaded_file(saved_path)
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(400, f"Error parsing dataset: {str(e)}")

    if df.empty or len(df.columns) == 0:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(400, "The uploaded dataset is empty.")

    # Store normalized CSV for reliable cross-engine processing
    csv_path = UPLOAD_DIR / f"{file_id}.csv"
    df.to_csv(csv_path, index=False)
    DATASET_CACHE[file_id] = df

    # Run TypeSafe Jev Schema Classification
    detector = JevColumnDetector(api_key=typesafe_key)
    classification = detector.classify_table(df)

    PROFILE_CACHE[file_id] = classification["company_profile"]

    preview_rows = df.head(8).fillna("").to_dict(orient="records")

    return {
        "status": "ok",
        "file_id": file_id,
        "filename": file.filename,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "detected_mapping": classification["detected_mapping"],
        "column_meta": classification["column_meta"],
        "company_profile": classification["company_profile"],
        "jev_enabled": classification["jev_enabled"],
        "preview": preview_rows
    }


@app.post("/api/load-sample")
async def load_sample_dataset(typesafe_key: Optional[str] = Form(None)):
    """Loads the pre-bundled realistic Kaggle-style retail e-commerce dataset for instant 1-click testing."""
    if not SAMPLE_FILE.exists():
        generate_sample_dataset(SAMPLE_FILE)

    file_id = f"sample_{uuid.uuid4().hex[:8]}"
    df = pd.read_csv(SAMPLE_FILE)
    DATASET_CACHE[file_id] = df

    # Run TypeSafe Jev Schema Classification
    detector = JevColumnDetector(api_key=typesafe_key)
    classification = detector.classify_table(df)
    PROFILE_CACHE[file_id] = classification["company_profile"]

    return {
        "status": "ok",
        "file_id": file_id,
        "filename": "Global_Ecommerce_Sales_Kaggle.csv",
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "detected_mapping": classification["detected_mapping"],
        "column_meta": classification["column_meta"],
        "company_profile": classification["company_profile"],
        "jev_enabled": classification["jev_enabled"],
        "preview": df.head(8).fillna("").to_dict(orient="records")
    }


@app.post("/api/analyze")
async def run_analysis(
    file_id: str = Form(...),
    mapping: str = Form(...)  # JSON string of standard_field -> column_name
):
    """
    Executes full multi-dimensional analytics: KPIs, Monthly Trends, RFM Customer
    Segmentation, Product & Geo Affinity, and Holt-Winters Forecasting.
    """
    df = DATASET_CACHE.get(file_id)
    if df is None:
        csv_path = UPLOAD_DIR / f"{file_id}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            DATASET_CACHE[file_id] = df
        elif file_id.startswith("sample_") and SAMPLE_FILE.exists():
            df = pd.read_csv(SAMPLE_FILE)
            DATASET_CACHE[file_id] = df
        else:
            raise HTTPException(404, "Session expired or file_id not found. Please upload again.")

    try:
        mapping_dict = json.loads(mapping) if isinstance(mapping, str) else mapping
    except Exception:
        raise HTTPException(400, "Invalid mapping JSON.")

    bi_engine = NexusBIEngine(df, mapping_dict)
    analytics_result = bi_engine.compute_all_analytics()
    analytics_result["file_id"] = file_id
    analytics_result["company_profile"] = PROFILE_CACHE.get(file_id, {})

    return JSONResponse(analytics_result)


@app.post("/api/predict")
async def run_predict(
    file_id: str = Form(...),
    mapping: str = Form(...),
    target: str = Form("sales"),
    periods: int = Form(6, ge=1, le=24)
):
    """Generates custom forecasting projections for a chosen metric and horizon."""
    df = DATASET_CACHE.get(file_id)
    if df is None:
        csv_path = UPLOAD_DIR / f"{file_id}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            DATASET_CACHE[file_id] = df
        elif file_id.startswith("sample_") and SAMPLE_FILE.exists():
            df = pd.read_csv(SAMPLE_FILE)
            DATASET_CACHE[file_id] = df
        else:
            raise HTTPException(404, "Session not found.")

    try:
        mapping_dict = json.loads(mapping) if isinstance(mapping, str) else mapping
    except Exception:
        raise HTTPException(400, "Invalid mapping JSON.")

    bi_engine = NexusBIEngine(df, mapping_dict)
    forecast_result = bi_engine.compute_forecast(target_metric=target, periods=periods)
    forecast_result["file_id"] = file_id
    return JSONResponse(forecast_result)


@app.post("/api/news")
async def get_live_news(
    file_id: Optional[str] = Form(None),
    company_profile: Optional[str] = Form(None),
    custom_query: Optional[str] = Form(None)
):
    """
    Fetches live news based on the inferred company products and regions,
    running the AI decision automation model for supply chain, tariffs, festive demand,
    and regional crises.
    """
    profile = {}
    if company_profile:
        try:
            profile = json.loads(company_profile)
        except Exception:
            profile = {}
    elif file_id and file_id in PROFILE_CACHE:
        profile = PROFILE_CACHE[file_id]

    if not profile:
        profile = {
            "industry": "Global Omnichannel Commerce & Retail",
            "primary_categories": ["Consumer Goods", "Hardware", "Logistics"],
            "operating_regions": ["North America", "Europe", "Asia-Pacific"]
        }

    news_data = await news_engine.fetch_and_analyze(profile, custom_query=custom_query)
    return JSONResponse(news_data)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav_path = FRONTEND_DIR / "favicon.svg"
    if fav_path.exists():
        return FileResponse(fav_path, media_type="image/svg+xml")
    return JSONResponse(status_code=204, content={})


# Serve frontend static assets directly at root
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
