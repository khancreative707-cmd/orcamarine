from typing import Tuple, Dict, Any, Optional

def get_beaufort_scale(wind_speed_kmh: float) -> Dict[str, Any]:
    """
    Maps wind speed in km/h to the official World Meteorological Organization (WMO) Beaufort Wind Scale.
    Returns: force (0-12), name, and sea effect description.
    """
    if wind_speed_kmh < 1.0:
        return {"force": 0, "name": "Calm", "sea_description": "Sea like a mirror"}
    elif wind_speed_kmh <= 5.0:
        return {"force": 1, "name": "Light Air", "sea_description": "Ripples without crests"}
    elif wind_speed_kmh <= 11.0:
        return {"force": 2, "name": "Light Breeze", "sea_description": "Small wavelets, glassy crests"}
    elif wind_speed_kmh <= 19.0:
        return {"force": 3, "name": "Gentle Breeze", "sea_description": "Large wavelets, scattered whitecaps"}
    elif wind_speed_kmh <= 28.0:
        return {"force": 4, "name": "Moderate Breeze", "sea_description": "Small waves, frequent whitecaps"}
    elif wind_speed_kmh <= 38.0:
        return {"force": 5, "name": "Fresh Breeze", "sea_description": "Moderate waves, many whitecaps, some spray"}
    elif wind_speed_kmh <= 49.0:
        return {"force": 6, "name": "Strong Breeze", "sea_description": "Large waves forming, extensive whitecaps and spray"}
    elif wind_speed_kmh <= 61.0:
        return {"force": 7, "name": "Near Gale", "sea_description": "Sea heaps up, white foam begins to be blown in streaks"}
    elif wind_speed_kmh <= 74.0:
        return {"force": 8, "name": "Gale", "sea_description": "Moderately high waves, breaking crests form spindrift"}
    elif wind_speed_kmh <= 88.0:
        return {"force": 9, "name": "Strong Gale", "sea_description": "High waves, dense foam streaks, reduced visibility"}
    elif wind_speed_kmh <= 102.0:
        return {"force": 10, "name": "Storm", "sea_description": "Very high waves with long overhanging crests"}
    elif wind_speed_kmh <= 117.0:
        return {"force": 11, "name": "Violent Storm", "sea_description": "Exceptionally high waves, visibility badly affected"}
    else:
        return {"force": 12, "name": "Hurricane", "sea_description": "Air filled with foam and driving spray, sea completely white"}

def get_douglas_sea_state(wave_height_m: float) -> Dict[str, Any]:
    """
    Maps significant wave height in meters to the Douglas Sea Scale.
    """
    if wave_height_m < 0.1:
        return {"code": 0, "description": "Calm (glassy)"}
    elif wave_height_m <= 0.5:
        return {"code": 1, "description": "Calm (rippled)"}
    elif wave_height_m <= 1.25:
        return {"code": 2, "description": "Smooth (wavelets)"}
    elif wave_height_m <= 2.5:
        return {"code": 3, "description": "Slight to Moderate"}
    elif wave_height_m <= 4.0:
        return {"code": 4, "description": "Rough"}
    elif wave_height_m <= 6.0:
        return {"code": 5, "description": "Very Rough"}
    elif wave_height_m <= 9.0:
        return {"code": 6, "description": "High"}
    elif wave_height_m <= 14.0:
        return {"code": 7, "description": "Very High"}
    else:
        return {"code": 8, "description": "Phenomenal"}

def calculate_gust_volatility(wind_speed_kmh: float, wind_gusts_kmh: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculates gust factor volatility (gusts / wind) to detect sudden squall and microburst risks.
    """
    if not wind_gusts_kmh or wind_speed_kmh <= 2.0:
        return {"gust_factor": 1.0, "squall_risk": "Low", "description": "Steady wind flow"}
    
    factor = round(wind_gusts_kmh / wind_speed_kmh, 2)
    if factor >= 1.7:
        return {"gust_factor": factor, "squall_risk": "High", "description": "Violent squall turbulence; sudden microburst capsize hazard"}
    elif factor >= 1.4:
        return {"gust_factor": factor, "squall_risk": "Moderate", "description": "Puffy gusts requiring attentive helm control"}
    else:
        return {"gust_factor": factor, "squall_risk": "Low", "description": "Stable wind envelope"}

VESSEL_THRESHOLDS = {
    "kayak_canoe": {
        "max_wave_m": 0.8,
        "caution_wave_m": 0.5,
        "max_wind_kmh": 18.0,
        "caution_wind_kmh": 12.0,
        "label": "Kayak / Canoe / Paddlecraft",
    },
    "small_craft": {
        "max_wave_m": 1.8,
        "caution_wave_m": 1.2,
        "max_wind_kmh": 28.0,
        "caution_wind_kmh": 18.0,
        "label": "18–25ft Motorized Skiff / Fishing Boat",
    },
    "commercial_trawler": {
        "max_wave_m": 3.0,
        "caution_wave_m": 2.0,
        "max_wind_kmh": 42.0,
        "caution_wind_kmh": 28.0,
        "label": "Mechanized Commercial Trawler (>35ft)",
    },
    "passenger_ferry": {
        "max_wave_m": 2.5,
        "caution_wave_m": 1.8,
        "max_wind_kmh": 35.0,
        "caution_wind_kmh": 24.0,
        "label": "Passenger Ferry / Coastal Transport",
    },
    "general": {
        "max_wave_m": 2.2,
        "caution_wave_m": 1.4,
        "max_wind_kmh": 32.0,
        "caution_wind_kmh": 20.0,
        "label": "General Coastal Marine Vessel",
    },
}

def evaluate_vessel_safety(
    vessel_type: str,
    wave_height_m: float,
    wind_speed_kmh: float,
    wind_gusts_kmh: Optional[float] = None,
    mpa_distance_km: Optional[float] = None,
    inside_mpa: bool = False,
    sanctuary_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates safety against tailored nautical stability limits for the specific craft type.
    """
    v_key = vessel_type.lower().strip()
    if "kayak" in v_key or "canoe" in v_key or "paddle" in v_key:
        thresholds = VESSEL_THRESHOLDS["kayak_canoe"]
    elif "trawler" in v_key or "ship" in v_key or "commercial" in v_key:
        thresholds = VESSEL_THRESHOLDS["commercial_trawler"]
    elif "ferry" in v_key or "passenger" in v_key:
        thresholds = VESSEL_THRESHOLDS["passenger_ferry"]
    elif "small" in v_key or "skiff" in v_key or "dinghy" in v_key or "boat" in v_key or "fish" in v_key:
        thresholds = VESSEL_THRESHOLDS["small_craft"]
    else:
        thresholds = VESSEL_THRESHOLDS["general"]

    is_unsafe = False
    is_caution = False
    score = 15
    reasons = []

    # 1. Wave Evaluation
    if wave_height_m >= thresholds["max_wave_m"]:
        is_unsafe = True
        score = max(score, 85)
        reasons.append(f"Wave height of {wave_height_m} m exceeds safe envelope for {thresholds['label']} (limit: {thresholds['max_wave_m']} m).")
    elif wave_height_m >= thresholds["caution_wave_m"]:
        is_caution = True
        score = max(score, 50)
        reasons.append(f"Wave height of {wave_height_m} m approaches upper limit for {thresholds['label']}.")
    else:
        reasons.append(f"Wave height of {wave_height_m} m is favorable for {thresholds['label']}.")

    # 2. Wind Evaluation
    if wind_speed_kmh >= thresholds["max_wind_kmh"]:
        is_unsafe = True
        score = max(score, 85)
        reasons.append(f"Wind speed of {wind_speed_kmh} km/h is hazardous for {thresholds['label']} (limit: {thresholds['max_wind_kmh']} km/h).")
    elif wind_speed_kmh >= thresholds["caution_wind_kmh"]:
        if not is_unsafe:
            is_caution = True
        score = max(score, 50)
        reasons.append(f"Wind speed of {wind_speed_kmh} km/h generates significant surface chop for {thresholds['label']}.")
    else:
        reasons.append(f"Wind speed of {wind_speed_kmh} km/h is calm and manageable.")

    # 3. Gust Volatility
    gust_info = calculate_gust_volatility(wind_speed_kmh, wind_gusts_kmh)
    if gust_info["squall_risk"] == "High":
        if not is_unsafe:
            is_caution = True
        score = max(score, 65)
        reasons.append(f"Squall Warning: Gust factor of {gust_info['gust_factor']} ({wind_gusts_kmh} km/h peak) threatens small craft stability.")

    # 4. Marine Protected Area Boundary
    if inside_mpa or (mpa_distance_km is not None and mpa_distance_km < 5.0):
        if not is_unsafe:
            is_caution = True
        score = max(score, 55)
        reasons.append(f"Proximity alert: Operating {mpa_distance_km} km from {sanctuary_name or 'Marine Sanctuary'} protected boundary.")

    verdict = "UNSAFE" if is_unsafe else ("CAUTION" if is_caution else "SAFE")
    beaufort = get_beaufort_scale(wind_speed_kmh)
    sea_state = get_douglas_sea_state(wave_height_m)

    return {
        "verdict": verdict,
        "risk_score": score,
        "vessel_class": thresholds["label"],
        "beaufort": beaufort,
        "sea_state": sea_state,
        "gust_analysis": gust_info,
        "reasons": reasons,
    }
