import json
from pathlib import Path
from typing import Optional, Tuple
from shapely.geometry import shape, Point

_MPA_CACHE = None

def _load_features():
    global _MPA_CACHE
    if _MPA_CACHE is not None:
        return _MPA_CACHE

    possible_paths = [
        Path("data/mpa.geojson"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "mpa.geojson",
    ]

    for p in possible_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    gj = json.load(f)
                    _MPA_CACHE = [
                        (
                            shape(feat["geometry"]),
                            feat.get("properties", {}).get("name")
                            or feat.get("properties", {}).get("NAME")
                            or "Marine Sanctuary",
                        )
                        for feat in gj.get("features", [])
                        if feat.get("geometry")
                    ]
                    return _MPA_CACHE
            except Exception:
                pass

    _MPA_CACHE = []
    return _MPA_CACHE

def calculate_mpa_distance(latitude: float, longitude: float) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Computes distance in km to nearest Marine Protected Area using Shapely geometries.
    Returns: (distance_km, nearest_sanctuary_name, is_inside)
    """
    features = _load_features()
    if not features:
        return None, None, False

    point = Point(longitude, latitude)
    min_dist_km = float("inf")
    nearest_name = None

    for geom, name in features:
        if geom.contains(point) or geom.touches(point):
            return 0.0, name, True
        dist = geom.distance(point) * 111.12
        if dist < min_dist_km:
            min_dist_km = dist
            nearest_name = name

    if min_dist_km != float("inf"):
        return round(min_dist_km, 1), nearest_name, False

    return None, None, False
