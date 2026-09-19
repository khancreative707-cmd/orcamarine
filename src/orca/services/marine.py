from typing import Optional
import httpx

def fetch_live_marine(latitude: float, longitude: float, forecast_day: int = 0) -> Optional[float]:
    """
    Fetches real-time or forecasted wave height in meters from Open-Meteo Marine API.
    - forecast_day=0: current/today wave height
    - forecast_day=1: tomorrow's forecast wave height
    - forecast_day=2: day after tomorrow forecast
    Returns wave_height_m as float, or None if unreachable.
    """
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wave_height,wave_direction,wave_period",
        "daily": "wave_height_max",
        "forecast_days": max(3, forecast_day + 1),
        "timezone": "auto",
    }
    headers = {"User-Agent": "ORCAMarine-Hackathon/1.0"}
    try:
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if forecast_day == 0:
                    current = data.get("current", {})
                    wave = current.get("wave_height")
                    if wave is not None:
                        return round(float(wave), 1)
                daily = data.get("daily", {})
                daily_waves = daily.get("wave_height_max", [])
                if daily_waves and len(daily_waves) > forecast_day:
                    val = daily_waves[forecast_day]
                    if val is not None:
                        return round(float(val), 1)
    except Exception:
        pass
    return None
