from typing import Optional, Dict, Any

MANGALURU_SAFE_FIXTURE: Dict[str, Any] = {
    "status": "ok",
    "questionType": "sea_conditions",
    "location": {
        "name": "Mangaluru",
        "lat": 12.87,
        "lon": 74.88,
    },
    "verdict": "SAFE",
    "riskScore": 18,
    "reasons": [
        "Wind speed is calm at 14.2 km/h.",
        "Wave height is low at 0.8 m.",
        "Distance to nearest Marine Protected Area is 18.5 km.",
    ],
    "data": {
        "windSpeedKmh": 14.2,
        "waveHeightM": 0.8,
        "mpaDistanceKm": 18.5,
    },
    "explanation": (
        "Current sea conditions off Mangaluru are calm and favorable, with gentle winds of 14.2 km/h "
        "and a low wave height of 0.8 m. You are also situated 18.5 km away from the nearest marine "
        "protected zone, making it safe for small craft navigation and coastal boating today."
    ),
    "sources": [
        {
            "name": "Open-Meteo Weather API",
            "url": "https://open-meteo.com/en/docs",
        },
        {
            "name": "Open-Meteo Marine API",
            "url": "https://open-meteo.com/en/docs/marine-weather-api",
        },
        {
            "name": "Protected Planet Marine Dataset",
            "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas",
        },
    ],
}

GOA_CAUTION_FIXTURE: Dict[str, Any] = {
    "status": "ok",
    "questionType": "protected_area",
    "location": {
        "name": "Goa",
        "lat": 15.49,
        "lon": 73.82,
    },
    "verdict": "CAUTION",
    "riskScore": 55,
    "reasons": [
        "Within 2.1 km of Netravali Marine Sanctuary boundary.",
        "Wind speed is moderate at 22.0 km/h.",
        "Wave height is moderate at 1.4 m.",
    ],
    "data": {
        "windSpeedKmh": 22.0,
        "waveHeightM": 1.4,
        "mpaDistanceKm": 2.1,
    },
    "explanation": (
        "Caution is strongly advised off the coast of Goa because you are only 2.1 km from the protected "
        "boundary of Netravali Marine Sanctuary, where regulated fishing and entry restrictions apply. "
        "While ocean conditions are moderate with 22.0 km/h winds and 1.4 m waves, vessel operators must "
        "ensure they do not drift across sanctuary lines."
    ),
    "sources": [
        {
            "name": "Open-Meteo Weather API",
            "url": "https://open-meteo.com/en/docs",
        },
        {
            "name": "Open-Meteo Marine API",
            "url": "https://open-meteo.com/en/docs/marine-weather-api",
        },
        {
            "name": "Protected Planet Marine Dataset",
            "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas",
        },
    ],
}

MUMBAI_UNSAFE_FIXTURE: Dict[str, Any] = {
    "status": "ok",
    "questionType": "sea_conditions",
    "location": {
        "name": "Mumbai",
        "lat": 18.92,
        "lon": 72.83,
    },
    "verdict": "UNSAFE",
    "riskScore": 88,
    "reasons": [
        "Wave height exceeds safe threshold at 3.6 m.",
        "Wind speed is hazardous at 48.5 km/h.",
        "Distance to nearest Marine Protected Area is 12.0 km.",
    ],
    "data": {
        "windSpeedKmh": 48.5,
        "waveHeightM": 3.6,
        "mpaDistanceKm": 12.0,
    },
    "explanation": (
        "Maritime conditions off Mumbai are currently classified as UNSAFE due to severe weather hazards, "
        "featuring turbulent wave heights of 3.6 m and dangerous gale-force winds of 48.5 km/h. "
        "Small craft advisories are active, and all non-essential recreational boating and fishing "
        "operations should be suspended immediately until sea states normalize."
    ),
    "sources": [
        {
            "name": "Open-Meteo Weather API",
            "url": "https://open-meteo.com/en/docs",
        },
        {
            "name": "Open-Meteo Marine API",
            "url": "https://open-meteo.com/en/docs/marine-weather-api",
        },
        {
            "name": "Protected Planet Marine Dataset",
            "url": "https://www.protectedplanet.net/en/thematic-areas/marine-protected-areas",
        },
    ],
}

DEMO_FIXTURES = {
    "mangaluru": MANGALURU_SAFE_FIXTURE,
    "mangalore": MANGALURU_SAFE_FIXTURE,
    "goa": GOA_CAUTION_FIXTURE,
    "mumbai": MUMBAI_UNSAFE_FIXTURE,
}

def get_demo_fixture(question: str) -> Optional[Dict[str, Any]]:
    """
    Matches an incoming question to one of the three rehearsed demo fixtures.
    Strictly matches only the rehearsed city names; returns None for any other city.
    """
    q = question.lower()
    if "goa" in q or "netravali" in q:
        return GOA_CAUTION_FIXTURE
    if "mumbai" in q or "bombay" in q:
        return MUMBAI_UNSAFE_FIXTURE
    if "mangaluru" in q or "mangalore" in q:
        return MANGALURU_SAFE_FIXTURE
    
    # Do NOT return a fixture if the query mentions another city (e.g. San Francisco)
    return None
