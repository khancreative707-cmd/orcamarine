import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger("orca.teammate_client")

DEFAULT_TEAMMATE_URL = "https://orcamarine-backend.onrender.com"

def query_teammate_backend(location_name: str, question: str = "") -> Optional[Dict[str, Any]]:
    """
    Queries Teammate B's deployed Render service at https://orcamarine-backend.onrender.com/ask.
    Extracts coordinates, marine wave data, and weather telemetry directly from the cloud.
    """
    base_url = os.environ.get("TEAMMATE_BACKEND_URL", DEFAULT_TEAMMATE_URL).rstrip("/")
    url = f"{base_url}/ask"

    payload = {
        "location": location_name,
        "question": question or f"What are the marine conditions near {location_name}?",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                loc = data.get("location", {})
                weather = data.get("weather", {})
                marine = data.get("marine", {})
                mpa = data.get("protected_area", {})
                safety = data.get("safety", {})

                lat = loc.get("latitude")
                lon = loc.get("longitude")
                display_name = loc.get("resolved_name") or location_name

                wind = weather.get("wind_speed_kmh")
                wave = marine.get("wave_height_m")
                inside_mpa = mpa.get("inside_mpa", False)
                errors = data.get("errors", [])
                if errors:
                    logger.info(f"Teammate B cloud API reported notes: {errors}")

                return {
                    "location": {"lat": lat, "lon": lon, "name": display_name},
                    "wind": wind,
                    "wave": wave,
                    "inside_mpa": inside_mpa,
                    "reasons": safety.get("reasons", []),
                    "errors": errors,
                    "raw": data,
                }
    except Exception as e:
        logger.warning(f"Could not reach Teammate B's cloud API at {url}: {e}")

    return None
