from typing import Tuple, Optional
import httpx

KNOWN_COASTAL_CITIES = {
    "mangaluru": (12.87, 74.88, "Mangaluru, Karnataka, India"),
    "mangalore": (12.87, 74.88, "Mangaluru, Karnataka, India"),
    "goa": (15.49, 73.82, "Goa, India"),
    "mumbai": (18.92, 72.83, "Mumbai, Maharashtra, India"),
    "bombay": (18.92, 72.83, "Mumbai, Maharashtra, India"),
    "kochi": (9.93, 76.26, "Kochi, Kerala, India"),
    "cochin": (9.93, 76.26, "Kochi, Kerala, India"),
    "chennai": (13.08, 80.27, "Chennai, Tamil Nadu, India"),
    "madras": (13.08, 80.27, "Chennai, Tamil Nadu, India"),
    "visakhapatnam": (17.68, 83.21, "Visakhapatnam, Andhra Pradesh, India"),
    "vizag": (17.68, 83.21, "Visakhapatnam, Andhra Pradesh, India"),
    "karwar": (14.81, 74.13, "Karwar, Karnataka, India"),
    "kolkata": (22.57, 88.36, "Kolkata, West Bengal, India"),
    "san francisco": (37.77, -122.41, "San Francisco, California, USA"),
}

def geocode_location(location_name: str) -> Tuple[float, float, str]:
    """
    Resolves a location name to (latitude, longitude, resolved_name).
    Checks known coastal cache first, then queries OpenStreetMap Nominatim.
    """
    key = location_name.strip().lower()
    if key in KNOWN_COASTAL_CITIES:
        return KNOWN_COASTAL_CITIES[key]

    # Query Nominatim API with user-agent
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": location_name, "format": "jsonv2", "limit": 1}
        headers = {"User-Agent": "ORCAMarine-Project/1.0 (sih.orca.marine@gmail.com)"}
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200 and resp.json():
                item = resp.json()[0]
                return float(item["lat"]), float(item["lon"]), item.get("display_name", location_name.title())
    except Exception:
        pass

    # Safe fallback if offline or unreachable
    return 13.00, 75.00, location_name.strip().title()
