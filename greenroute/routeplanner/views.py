import logging
import requests
import json

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Avg, Count
from django.contrib.auth.models import User

from adminpanel.models import RouteHistory

logger = logging.getLogger(__name__)

# -------------------------
# Config
# -------------------------
ORS_API_KEY = getattr(settings, "ORS_API_KEY", "") or getattr(settings, "OPENROUTESERVICE_API_KEY", "")
ORS_API_KEY = ORS_API_KEY.strip() if isinstance(ORS_API_KEY, str) else ""
AGRO_API_KEY = getattr(settings, "AGRO_API_KEY", "")

# -------------------------
# Helper functions
# -------------------------
def ors_geocode(place):
    try:
        resp = requests.get(
            "https://api.openrouteservice.org/geocode/search",
            params={"api_key": ORS_API_KEY, "text": place, "size": 1},
            timeout=8
        )
        if resp.status_code == 403:
            return {"forbidden": True}
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if not features:
            return None
        lon, lat = features[0]["geometry"]["coordinates"]
        return (lat, lon)
    except Exception as e:
        logger.error(f"ORS geocode error: {e}")
        return None

def ors_route(slat, slon, dlat, dlon):
    try:
        resp = requests.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
            json={"coordinates": [[slon, slat], [dlon, dlat]]},
            timeout=12
        )
        if resp.status_code == 403:
            return {"forbidden": True}
        resp.raise_for_status()
        feat = resp.json()["features"][0]
        coords = [[lat, lon] for lon, lat in feat["geometry"]["coordinates"]]
        dist_km = round(feat["properties"]["segments"][0]["distance"] / 1000, 3)
        return {"distance_km": dist_km, "coords": coords}
    except Exception as e:
        logger.error(f"ORS route error: {e}")
        return None

def nominatim_geocode(place):
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place, "format": "json", "limit": 1},
            headers={"User-Agent": "GreenRoute/1.0"},
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        return (float(data[0]["lat"]), float(data[0]["lon"]))
    except Exception as e:
        logger.error(f"Nominatim geocode error: {e}")
        return None

def osrm_route(slat, slon, dlat, dlon):
    try:
        resp = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{slon},{slat};{dlon},{dlat}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=12
        )
        resp.raise_for_status()
        route = resp.json()["routes"][0]
        coords = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
        dist_km = round(route["distance"] / 1000, 3)
        return {"distance_km": dist_km, "coords": coords}
    except Exception as e:
        logger.error(f"OSRM route error: {e}")
        return None

def get_green_cover(lat, lon):
    try:
        if not AGRO_API_KEY:
            return 70.0
        poly_url = "http://api.agromonitoring.com/agro/1.0/polygons"
        poly_body = {
            "name": "point_area",
            "geo_json": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon - 0.01, lat - 0.01],
                        [lon - 0.01, lat + 0.01],
                        [lon + 0.01, lat + 0.01],
                        [lon + 0.01, lat - 0.01],
                        [lon - 0.01, lat - 0.01]
                    ]]
                }
            }
        }
        poly_resp = requests.post(poly_url, json=poly_body, params={"appid": AGRO_API_KEY}, timeout=12)
        poly_resp.raise_for_status()
        poly_id = poly_resp.json().get("id")
        if not poly_id:
            return 70.0
        ndvi_url = "http://api.agromonitoring.com/agro/1.0/ndvi/history"
        ndvi_resp = requests.get(ndvi_url, params={"polyid": poly_id, "appid": AGRO_API_KEY}, timeout=12)
        ndvi_resp.raise_for_status()
        ndvi_data = ndvi_resp.json()
        if isinstance(ndvi_data, list) and ndvi_data:
            ndvi = ndvi_data[-1].get("mean", 0)
            return round(max(0, min(100, (ndvi + 1) * 50)), 1)
    except Exception as e:
        logger.error(f"Agro API error: {e}")
    return 70.0

def compute_eco_metrics(distance_km, src_lat, src_lon, dst_lat, dst_lon):
    pollution_index = min(100.0, round((distance_km / 500) * 100, 2))
    g_src = get_green_cover(src_lat, src_lon)
    g_dst = get_green_cover(dst_lat, dst_lon)
    green_cover = round((g_src + g_dst) / 2, 1)
    eco_score = round(max(0.0, min(100.0, (green_cover * 0.7) - (pollution_index * 0.3))), 2)
    eco_cost = round(100.0 - eco_score, 2)
    return pollution_index, green_cover, eco_score, eco_cost

# -------------------------
# Views
# -------------------------
@login_required
def index_view(request):
    ctx = {}
    if request.method == "POST":
        src = request.POST.get("source", "").strip()
        dst = request.POST.get("destination", "").strip()
        if not src or not dst:
            ctx["error"] = "Please enter both source and destination."
            return render(request, "index.html", ctx)

        use_ors = bool(ORS_API_KEY)
        s = ors_geocode(src) if use_ors else nominatim_geocode(src)
        d = ors_geocode(dst) if use_ors else nominatim_geocode(dst)
        if s == {"forbidden": True} or d == {"forbidden": True}:
            use_ors = False
            s, d = nominatim_geocode(src), nominatim_geocode(dst)
        if not s or not d:
            ctx["error"] = "Could not find location."
            return render(request, "index.html", ctx)

        r = ors_route(s[0], s[1], d[0], d[1]) if use_ors else osrm_route(s[0], s[1], d[0], d[1])
        if r == {"forbidden": True} or not r:
            r = osrm_route(s[0], s[1], d[0], d[1])
        if not r:
            ctx["error"] = "Could not fetch route."
            return render(request, "index.html", ctx)

        pollution_index, green_cover, eco_score, eco_cost = compute_eco_metrics(r["distance_km"], s[0], s[1], d[0], d[1])

        try:
            RouteHistory.objects.create(
                user=request.user,
                source=src,
                destination=dst,
                distance_km=r["distance_km"],
                pollution_index=pollution_index,
                green_cover=green_cover,
                eco_cost=eco_cost
            )
        except Exception as e:
            logger.error(f"Failed to save RouteHistory: {e}")

        # Prepare Leaflet-friendly route data
        route_line = {
            "coords": r["coords"],
            "color": "green" if green_cover >= 70 else "yellow" if green_cover >= 40 else "red",
            "weight": 6 if green_cover >= 70 else 4
        }

        ctx.update({
            "source": src,
            "destination": dst,
            "distance": r["distance_km"],
            "pollution_index": f"{pollution_index}%",
            "green_cover": f"{green_cover}%",
            "eco_score": f"{eco_score}%",
            "eco_cost": f"{eco_cost}%",
            "route_data": json.dumps(route_line)
        })
    return render(request, "index.html", ctx)

@login_required
def route_api_view(request):
    src = request.GET.get("source", "").strip()
    dst = request.GET.get("destination", "").strip()
    if not src or not dst:
        return JsonResponse({"error": "Source and destination required"}, status=400)

    use_ors = bool(ORS_API_KEY)
    s = ors_geocode(src) if use_ors else nominatim_geocode(src)
    d = ors_geocode(dst) if use_ors else nominatim_geocode(dst)
    if s == {"forbidden": True} or d == {"forbidden": True} or not s or not d:
        use_ors = False
        s, d = nominatim_geocode(src), nominatim_geocode(dst)
    if not s or not d:
        return JsonResponse({"error": "Invalid location"}, status=400)

    r = ors_route(s[0], s[1], d[0], d[1]) if use_ors else osrm_route(s[0], s[1], d[0], d[1])
    if r == {"forbidden": True} or not r:
        r = osrm_route(s[0], s[1], d[0], d[1])
    if not r:
        return JsonResponse({"error": "Could not fetch route"}, status=500)

    pollution_index, green_cover, eco_score, eco_cost = compute_eco_metrics(r["distance_km"], s[0], s[1], d[0], d[1])

    try:
        RouteHistory.objects.create(
            user=request.user,
            source=src,
            destination=dst,
            distance_km=r["distance_km"],
            pollution_index=pollution_index,
            green_cover=green_cover,
            eco_cost=eco_cost
        )
    except Exception as e:
        logger.error(f"Failed to save RouteHistory: {e}")

    route_line = {
        "coords": r["coords"],
        "color": "green" if green_cover >= 70 else "yellow" if green_cover >= 40 else "red",
        "weight": 6 if green_cover >= 70 else 4
    }

    return JsonResponse({
        "distance": r["distance_km"],
        "pollution_index": pollution_index,
        "green_cover": green_cover,
        "eco_score": eco_score,
        "eco_cost": eco_cost,
        "route_data": route_line
    })

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

@login_required
def custom_logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_routes = RouteHistory.objects.count()
    avg_ecocost = RouteHistory.objects.aggregate(avg=Avg('eco_cost'))['avg'] or 0
    pollution_data = list(RouteHistory.objects.order_by('-searched_at')[:10].values_list('pollution_index', flat=True))[::-1]
    popular_data = list(RouteHistory.objects.values('source', 'destination')
                        .annotate(count=Count('id')).order_by('-count')[:5])
    context = {
        "total_users": total_users,
        "total_routes": total_routes,
        "avg_ecocost": round(avg_ecocost, 2),
        "pollution_trends": json.dumps(pollution_data),
        "popular_routes": json.dumps(popular_data),
    }
    return render(request, "adminpanel/dashboard.html", context)
