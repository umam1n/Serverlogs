# FILE: sites/utils.py

from math import radians, sin, cos, sqrt, atan2

def is_user_in_range(user_lat, user_lon, site_lat, site_lon, radius_km=0.2):
    """
    Checks if a user's coordinates are within a given radius of a site's coordinates
    using the Haversine formula. Radius is in kilometers (default 0.2 km = 200 meters).
    """
    if not all([user_lat, user_lon, site_lat, site_lon]):
        return False # Cannot calculate if any coordinate is missing

    # Earth radius in kilometers
    R = 6371.0

    lat1, lon1 = radians(user_lat), radians(user_lon)
    lat2, lon2 = radians(site_lat), radians(site_lon)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance <= radius_km