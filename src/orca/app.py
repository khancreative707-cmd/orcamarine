import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.orca.planner import plan_query
from src.orca.synthesis import synthesize_explanation
from src.orca.rules_stub import evaluate_safety
from src.orca.fixtures import get_demo_fixture

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orca")

app = FastAPI(
    title="ORCA Marine Safety API",
    description="Backend service providing marine-safety Q&A, weather reasoning, and MPA proximity checks.",
    version="0.1.0",
)

# Enable CORS for Frontend (Teammate A: Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Contract Schemas (CONTRACT.md) ---

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        description="The user's raw marine-safety question.",
        json_schema_extra={"example": "Is it safe to take a small boat out near Mangaluru today?"},
    )
    simulate_broken_sources: Optional[List[str]] = Field(
        default=None,
        description="Optional list of sources to simulate as broken/unavailable (e.g. ['wave', 'mpa']).",
        json_schema_extra={"example": None},
    )
    demo_mode: Optional[bool] = Field(
        default=False,
        description="Set to true for offline rehearsed fixtures. Leave false for live AI analysis of any location.",
        json_schema_extra={"example": False},
    )

class LocationData(BaseModel):
    name: str
    lat: float
    lon: float

class MarineMetrics(BaseModel):
    windSpeedKmh: Optional[float] = None
    waveHeightM: Optional[float] = None
    mpaDistanceKm: Optional[float] = None

class SourceItem(BaseModel):
    name: str
    url: str

class AskResponse(BaseModel):
    status: Literal["ok", "unsupported", "missing_location", "error"]
    questionType: Optional[Literal["sea_conditions", "protected_area", "comparison", "unsupported"]] = None
    location: Optional[LocationData] = None
    verdict: Optional[Literal["SAFE", "CAUTION", "UNSAFE"]] = None
    riskScore: Optional[int] = None
    reasons: List[str] = Field(default_factory=list)
    data: Optional[MarineMetrics] = None
    explanation: str
    sources: List[SourceItem] = Field(default_factory=list)

# Standard contract redirect messages
UNSUPPORTED_EXPLANATION = (
    "I can only answer marine safety questions regarding current wind, wave conditions, "
    "and Marine Protected Areas for coastal cities. Please ask a question related to coastal marine safety."
)

MISSING_LOCATION_EXPLANATION = (
    "Please specify a coastal city or region (such as Mangaluru, Goa, or Mumbai) "
    "so I can retrieve live weather and marine boundary data for you."
)

ERROR_EXPLANATION = (
    "An unexpected error occurred while analyzing maritime conditions. "
    "Please try your request again shortly."
)

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"

@app.get("/", response_model=None)
def root(request: Request):
    """
    Root endpoint: serves the interactive visual dashboard to browsers,
    or returns API health check JSON for programmatic requests.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*") and STATIC_INDEX.exists():
        return FileResponse(STATIC_INDEX)
    return {"status": "ok", "service": "ORCA Marine Safety API"}

@app.get("/dashboard")
def dashboard():
    """Serves the standalone interactive HTML/Leaflet marine safety dashboard."""
    if STATIC_INDEX.exists():
        return FileResponse(STATIC_INDEX)
    raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/api/mpa-geojson")
def get_mpa_geojson():
    """Provides Marine Protected Areas GeoJSON for the interactive tactical map."""
    possible_paths = [
        Path("data/mpa.geojson"),
        Path(__file__).resolve().parent.parent.parent / "data" / "mpa.geojson",
    ]
    for p in possible_paths:
        if p.exists():
            return FileResponse(p, media_type="application/geo+json")
    raise HTTPException(status_code=404, detail="MPA GeoJSON not found")

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """
    Main ORCA endpoint implementing the full pipeline:
    1. DEMO_MODE: Offline rehearsed answers (skips LLM calls)
    2. Planner LLM Call: Extract location(s), target date, & classify questionType
    3. Data & Rules Engine: Deterministic verdict & live telemetry (supports comparison)
    4. Synthesis LLM Call: Natural language explanation with zero number hallucinations
    """
    try:
        # Check DEMO_MODE flag (either from request or environment)
        is_demo = (
            request.demo_mode is True or
            (request.demo_mode is None and os.environ.get("DEMO_MODE", "false").lower() in ("true", "1", "yes"))
        )

        if is_demo:
            fixture = get_demo_fixture(request.question)
            if fixture:
                return AskResponse(**fixture)

        # Step 1: Planner Step (LLM Call #1)
        planner_result = plan_query(request.question)
        question_type = planner_result.questionType
        location_name = planner_result.location
        comparison_locations = getattr(planner_result, "comparison_locations", [])
        target_date = getattr(planner_result, "target_date", "today")
        forecast_day = 1 if target_date == "tomorrow" else (2 if target_date == "future" else 0)

        # Handle unsupported queries
        if question_type == "unsupported":
            return AskResponse(
                status="unsupported",
                questionType="unsupported",
                location=None,
                verdict=None,
                riskScore=None,
                reasons=[],
                data=None,
                explanation=UNSUPPORTED_EXPLANATION,
                sources=[],
            )

        # Handle missing location queries
        if not location_name or not location_name.strip():
            return AskResponse(
                status="missing_location",
                questionType=question_type,
                location=None,
                verdict=None,
                riskScore=None,
                reasons=[],
                data=None,
                explanation=MISSING_LOCATION_EXPLANATION,
                sources=[],
            )

        # Step 2 & 3: Deterministic Data & Rules Engine (Primary Location)
        engine_result = evaluate_safety(
            location_name=location_name,
            question_type=question_type,
            broken_sources=request.simulate_broken_sources,
            forecast_day=forecast_day,
        )
        verdict = engine_result["verdict"]
        risk_score = engine_result["riskScore"]
        reasons = engine_result["reasons"]
        raw_data = engine_result["data"]
        raw_sources = engine_result["sources"]
        loc_coords = engine_result["location"]

        # If comparison locations are requested, evaluate secondary candidates
        comparison_data = []
        if comparison_locations:
            for comp_loc in comparison_locations:
                comp_res = evaluate_safety(
                    location_name=comp_loc,
                    question_type=question_type,
                    broken_sources=request.simulate_broken_sources,
                    forecast_day=forecast_day,
                )
                comparison_data.append({
                    "location_name": comp_res["location"]["name"],
                    "verdict": comp_res["verdict"],
                    "risk_score": comp_res["riskScore"],
                    "reasons": comp_res["reasons"],
                    "data": comp_res["data"],
                })
                for s in comp_res.get("sources", []):
                    if s not in raw_sources:
                        raw_sources.append(s)

        # Step 4: Synthesis Step (LLM Call #2)
        explanation = synthesize_explanation(
            location_name=loc_coords["name"],
            question_type=question_type,
            verdict=verdict,
            reasons=reasons,
            data=raw_data,
            risk_score=risk_score,
            comparison_data=comparison_data,
            target_date=target_date,
        )

        # Step 5: Construct and return Contract JSON
        return AskResponse(
            status="ok",
            questionType=question_type,
            location=LocationData(
                name=loc_coords["name"],
                lat=loc_coords["lat"],
                lon=loc_coords["lon"],
            ),
            verdict=verdict,
            riskScore=risk_score,
            reasons=reasons,
            data=MarineMetrics(
                windSpeedKmh=raw_data.get("windSpeedKmh"),
                waveHeightM=raw_data.get("waveHeightM"),
                mpaDistanceKm=raw_data.get("mpaDistanceKm"),
            ),
            explanation=explanation,
            sources=[SourceItem(name=s["name"], url=s["url"]) for s in raw_sources],
        )

    except Exception as e:
        logger.error(f"Error processing /ask: {e}", exc_info=True)
        return AskResponse(
            status="error",
            questionType=None,
            location=None,
            verdict=None,
            riskScore=None,
            reasons=[],
            data=None,
            explanation=ERROR_EXPLANATION,
            sources=[],
        )
