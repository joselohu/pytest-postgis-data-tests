"""Distance maths written without PostGIS, used as an independent check on the API."""

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_008.8

# PostGIS measures on the WGS84 spheroid and haversine on a sphere; the two differ by up to about 0.5%.
SPHERE_VS_SPHEROID_TOLERANCE = 0.006


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))
