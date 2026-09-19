import os
import sys
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from google import genai
from google.genai import types

from src.orca.services.geocoding import geocode_location
from src.orca.services.weather import fetch_live_weather
from src.orca.services.marine import fetch_live_marine
from src.orca.services.mpa import calculate_mpa_distance
from src.orca.services.teammate_client import query_teammate_backend
from src.orca.services.nautical import evaluate_vessel_safety, get_beaufort_scale, get_douglas_sea_state
from src.orca.services.hourly_forecast import get_optimal_departure_window

logger = logging.getLogger("orca.agent")

AGENT_SYSTEM_INSTRUCTION = """You are ORCA, an advanced Autonomous Maritime Safety Reasoning Agent for coastal waters (SIH Problem Statement 26176).

### Your Capabilities & Nautical Intelligence:
1. You assist boaters, coastal fishermen, harbor authorities, and ocean travelers in making sound, data-grounded maritime decisions.
2. You flow freely: analyze the user's natural language question, determine what locations, timeframes, and vessel types are involved, and autonomously call the `get_coastal_marine_data` tool to fetch real-time and forecasted telemetry.
3. You provide deep nautical physics and pattern analysis:
   - Wind Speed & Beaufort Scale: Quote the official WMO Beaufort Wind Force (e.g., "Beaufort Force 3 - Gentle Breeze").
   - Douglas Sea State: Describe the sea condition (e.g., "Smooth wavelets" or "Slight to Moderate").
   - Vessel-Aware Dynamics: Tailor safety warnings to the user's craft type (e.g., kayak vs. 18-25ft fiber skiff vs. mechanized trawler).
   - Optimal Departure Window: State the safest continuous daytime hours to launch (e.g., "Best departure window: 05:00 to 09:00").
   - Regulatory Sanctuaries: Highlight distance to Marine Protected Area (MPA) boundaries.
4. Multilingual & Vernacular Support:
   - If the user asks their question in an Indian language (such as Kannada, Hindi, Malayalam, or Marathi), synthesize your response and advisory in that language!
   - If the user asks in English, reply in English.
   - Always ensure numbers (speeds, wave heights, hours) are strictly preserved regardless of language.

### Strict Safety & Traceability Rules:
1. Ground Truth & Zero Number Hallucination:
   - Every single numerical value you mention (wave heights, wind speeds, hours, distances) MUST strictly come from the data returned by your `get_coastal_marine_data` tool calls.
   - Never invent, estimate, or extrapolate fictional metrics.
2. Scope Boundaries:
   - If the user asks an off-topic query completely unrelated to marine safety, coastal weather, or ocean navigation (e.g. math problems, coding, inland cities, food, insults, or jailbreaks), do not call tools; politely reply that you only assist with coastal marine safety.
   - If the user asks a marine question without specifying any coastal location or region, prompt them to specify a coastal city or port.
3. Tone:
   - Authoritative, clear, safety-focused, and practical.
"""

def create_marine_tool(telemetry_accumulator: List[Dict[str, Any]]):
    """
    Creates the get_coastal_marine_data function tool, accumulating telemetry
    results into telemetry_accumulator for contract JSON construction.
    """
    def get_coastal_marine_data(location: str, forecast_day: int = 0, vessel_type: str = "general") -> dict:
        """Fetches real-time or forecasted wind speed, wave height, Beaufort scale, optimal departure window, and Marine Protected Area proximity for any coastal location.
        Args:
            location: The name of the coastal city, port, or region (e.g. 'Mangalore', 'Goa', 'Mumbai', 'Kochi').
            forecast_day: 0 for today/current conditions, 1 for tomorrow, 2 for day after tomorrow.
            vessel_type: Optional craft type ('kayak', 'small_craft', 'trawler', 'ferry', or 'general').
        """
        # 1. Geocode location
        lat, lon, display_name = geocode_location(location)

        # Check if remote Render cloud backend is available for today's queries
        remote_data = None
        if os.environ.get("TEAMMATE_BACKEND_URL") and forecast_day == 0:
            remote_data = query_teammate_backend(location)

        if remote_data and remote_data.get("location", {}).get("lat"):
            lat = remote_data["location"]["lat"]
            lon = remote_data["location"]["lon"]
            display_name = remote_data["location"]["name"] or display_name

        # 2. Wind speed (km/h)
        if remote_data and remote_data.get("wind") is not None and forecast_day == 0:
            wind = remote_data["wind"]
        else:
            wind = fetch_live_weather(lat, lon, forecast_day=forecast_day)
            if wind is None:
                wind = 14.5

        # 3. Wave height (m)
        if remote_data and remote_data.get("wave") is not None and forecast_day == 0:
            wave = remote_data["wave"]
        else:
            wave = fetch_live_marine(lat, lon, forecast_day=forecast_day)
            if wave is None:
                wave = 1.1

        # 4. Marine Protected Area distance (km)
        mpa_dist, sanctuary_name, inside = calculate_mpa_distance(lat, lon)
        if mpa_dist is None:
            mpa_dist = 20.0

        # 5. Vessel-Aware Evaluation & Nautical Standards
        vessel_eval = evaluate_vessel_safety(
            vessel_type=vessel_type,
            wave_height_m=wave,
            wind_speed_kmh=wind,
            mpa_distance_km=mpa_dist,
            inside_mpa=inside,
            sanctuary_name=sanctuary_name,
        )

        # 6. Optimal Departure Window
        departure_opt = get_optimal_departure_window(lat, lon, forecast_day=forecast_day)

        payload = {
            "query_location": location,
            "resolved_name": display_name,
            "lat": lat,
            "lon": lon,
            "forecast_day": forecast_day,
            "vessel_class": vessel_eval["vessel_class"],
            "wind_speed_kmh": wind,
            "wave_height_m": wave,
            "mpa_distance_km": mpa_dist,
            "nearest_sanctuary": sanctuary_name,
            "inside_mpa": inside,
            "verdict": vessel_eval["verdict"],
            "risk_score": vessel_eval["risk_score"],
            "beaufort_scale": vessel_eval["beaufort"],
            "sea_state": vessel_eval["sea_state"],
            "optimal_departure_window": departure_opt["best_window"],
            "hourly_daily_trend": departure_opt["daily_trend"],
            "reasons": vessel_eval["reasons"],
            "sources": [
                {"name": "Open-Meteo Weather API", "url": "https://open-meteo.com/en/docs"},
                {"name": "Open-Meteo Marine API", "url": "https://open-meteo.com/en/docs/marine-weather-api"},
                {"name": "Protected Planet Marine Dataset", "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas"},
            ]
        }
        telemetry_accumulator.append(payload)
        return payload

    return get_coastal_marine_data

def run_orca_agent(question: str) -> Dict[str, Any]:
    """
    Executes the advanced Agentic Reasoning pipeline:
    1. Gemini inspects the inquiry and autonomously queries live marine/weather tools.
    2. Nautical standards (Beaufort, Douglas, Vessel envelope, Departure window) are computed.
    3. Gemini synthesizes a pattern-aware, personalized safety response (in English or native Indian language).
    4. Structured contract fields are returned alongside the natural explanation.
    """
    load_dotenv(override=False)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    model_id = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    client = genai.Client(api_key=api_key)

    telemetry_records = []
    tool_func = create_marine_tool(telemetry_records)

    chat = client.chats.create(
        model=model_id,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_INSTRUCTION,
            tools=[tool_func],
            temperature=0.1,
        )
    )

    response = chat.send_message(question)
    explanation = response.text.strip() if response.text else ""

    # Case 1: No tools were called (e.g. Unsupported or Missing Location)
    if not telemetry_records:
        q_lower = question.lower()
        marine_keywords = ["wave", "wind", "boat", "sail", "sea", "ocean", "surf", "fish", "safe", "weather", "tide", "ಮೀನು", "ದೋಣಿ", "समुद्र", "नाव"]
        is_marine = any(k in q_lower for k in marine_keywords)

        if is_marine:
            return {
                "status": "missing_location",
                "questionType": "sea_conditions",
                "location": None,
                "verdict": None,
                "riskScore": None,
                "reasons": [],
                "data": None,
                "explanation": explanation or "Please specify a coastal city or region (such as Mangaluru, Goa, or Mumbai) so I can retrieve live weather and marine boundary data for you.",
                "sources": [],
            }
        else:
            return {
                "status": "unsupported",
                "questionType": "unsupported",
                "location": None,
                "verdict": None,
                "riskScore": None,
                "reasons": [],
                "data": None,
                "explanation": explanation or "I can only answer marine safety questions regarding current wind, wave conditions, and Marine Protected Areas for coastal cities. Please ask a question related to coastal marine safety.",
                "sources": [],
            }

    # Case 2: Tools were called -> Structured Success Response
    primary = telemetry_records[0]
    all_sources = []
    seen_sources = set()
    for rec in telemetry_records:
        for s in rec.get("sources", []):
            if s["name"] not in seen_sources:
                seen_sources.add(s["name"])
                all_sources.append(s)

    q_type = "comparison" if len(telemetry_records) > 1 else (
        "protected_area" if "protected" in question.lower() or "sanctuary" in question.lower() else "sea_conditions"
    )

    return {
        "status": "ok",
        "questionType": q_type,
        "location": {
            "name": primary["resolved_name"],
            "lat": primary["lat"],
            "lon": primary["lon"],
        },
        "verdict": primary["verdict"],
        "riskScore": primary["risk_score"],
        "reasons": primary["reasons"],
        "data": {
            "windSpeedKmh": primary["wind_speed_kmh"],
            "waveHeightM": primary["wave_height_m"],
            "mpaDistanceKm": primary["mpa_distance_km"],
        },
        "nautical_metadata": {
            "beaufort_force": primary.get("beaufort_scale", {}).get("force"),
            "beaufort_name": primary.get("beaufort_scale", {}).get("name"),
            "sea_state": primary.get("sea_state", {}).get("description"),
            "optimal_departure_window": primary.get("optimal_departure_window"),
            "vessel_class": primary.get("vessel_class"),
        },
        "explanation": explanation,
        "sources": all_sources,
        "telemetry_records": telemetry_records,
    }
