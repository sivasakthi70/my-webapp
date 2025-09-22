import requests
import logging

logger = logging.getLogger(__name__)

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def get_green_cover(lat1, lon1, lat2, lon2, user_input=None):
    """
    Get green cover from multiple sources (user input, NDVI API, OSM Trees).
    Returns percentage (0–100).
    """

    # 1. User Input (highest priority if provided)
    if user_input is not None:
        logger.info(f"Using user-provided green cover: {user_input}%")
        return float(user_input)

    green_values = []

    # 2. NDVI API (Remote sensing)
    try:
        ndvi_url = f"https://api.agromonitoring.com/ndvi?lat1={lat1}&lon1={lon1}&lat2={lat2}&lon2={lon2}"
        resp = requests.get(ndvi_url, timeout=10)
        if resp.status_code == 200:
            ndvi_data = resp.json()
            if "green_cover" in ndvi_data:
                val = float(ndvi_data["green_cover"])
                green_values.append(val)
                logger.info(f"NDVI API green cover: {val}%")
    except Exception as e:
        logger.warning(f"NDVI API failed: {e}")

    # 3. OSM Trees Backup (Overpass API)
    try:
        query = f"""
        [out:json][timeout:25];
        (
          node["natural"="tree"](around:2000,{lat1},{lon1});
          node["natural"="tree"](around:2000,{lat2},{lon2});
          way["landuse"="forest"](around:2000,{lat1},{lon1});
          way["landuse"="forest"](around:2000,{lat2},{lon2});
        );
        out count;
        """
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=25)
        if response.status_code == 200:
            data = response.json()
            if "elements" in data:
                count = len(data["elements"])
                val = min(100, count / 50)  # scale: 50 trees = 100%
                green_values.append(val)
                logger.info(f"OSM Trees green cover: {val}%")
    except Exception as e:
        logger.warning(f"OSM API failed: {e}")


    # 4. Fallback Default
    if not green_values:
         logger.info("Using default green cover: 70%")
         return 70.0

    # 5. Average from available sources
    avg_val = sum(green_values) / len(green_values)
    return round(avg_val, 2)
