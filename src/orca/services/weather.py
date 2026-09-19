from typing import Optional
import httpx

def fetch_live_weather(latitude: float, longitude: float, forecast_day: int = 0) -> Optional[float]:
    """
    Fetches real-time wind speed in km/h from Open-Meteo Forecast API.
    - forecast_day=0: current/today wind speed
    - forecast_day=1: tomorrow's forecast wind speed
    - forecast_day=2: day after tomorrow forecast
    Returns wind_speed_kmh as float, or None if unreachable.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wind_speed_10m,wind_gusts_10m,temperature_2m",
        "daily": "wind_speed_10m_max",
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
                    wind = current.get("wind_speed_10m")
                    if wind is not None:
                        return round(float(wind), 1)
                daily = data.get("daily", {})
                daily_winds = daily.get("wind_speed_10m_max", [])
                if daily_winds and len(daily_winds) > forecast_day:
                    val = daily_winds[forecast_day]
                    if val is not None:
                        return round(float(val), 1)
    except Exception:
        pass
    return None
