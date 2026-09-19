from typing import Optional, Tuple
import httpx

def fetch_live_weather(latitude: float, longitude: float) -> Optional[float]:
    """
    Fetches real-time wind speed in km/h from the free Open-Meteo Forecast API.
    Returns wind_speed_kmh as float, or None if unreachable.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wind_speed_10m,wind_gusts_10m,temperature_2m",
        "timezone": "auto",
    }
    headers = {"User-Agent": "ORCAMarine-Hackathon/1.0"}
    try:
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                wind = current.get("wind_speed_10m")
                if wind is not None:
                    return round(float(wind), 1)
    except Exception:
        pass
    return None
