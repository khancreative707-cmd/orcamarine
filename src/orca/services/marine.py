from typing import Optional
import httpx

def fetch_live_marine(latitude: float, longitude: float) -> Optional[float]:
    """
    Fetches real-time wave height in meters from the free Open-Meteo Marine API.
    Returns wave_height_m as float, or None if unreachable.
    """
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wave_height,wave_direction,wave_period",
        "timezone": "auto",
    }
    headers = {"User-Agent": "ORCAMarine-Hackathon/1.0"}
    try:
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                wave = current.get("wave_height")
                if wave is not None:
                    return round(float(wave), 1)
    except Exception:
        pass
    return None
