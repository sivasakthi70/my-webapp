import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate

from adminpanel.models import RouteHistory

# ---------------------------
# Helper Functions
# ---------------------------
def is_admin(user):
    """Check if the user is staff or superuser."""
    return user.is_staff or user.is_superuser

# ---------------------------
# Admin Authentication
# ---------------------------
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()
        
        user = authenticate(request, username=username, password=password)
        if user and is_admin(user):
            login(request, user)
            return redirect("adminpanel:admin_dashboard")
        messages.error(request, "❌ Invalid credentials or not an admin.")
    return render(request, "adminpanel/login.html")


@login_required
@user_passes_test(is_admin)
def admin_logout(request):
    logout(request)
    return redirect("adminpanel:admin_login")


# ---------------------------
# Admin Dashboard
# ---------------------------
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_routes = RouteHistory.objects.count()
    avg_ecocost = RouteHistory.objects.aggregate(avg=Avg("eco_cost"))["avg"] or 0

    # Pollution trends by date
    pollution_qs = RouteHistory.objects.annotate(date=TruncDate("searched_at")) \
        .values("date").annotate(avg_pollution=Avg("pollution_index")).order_by("date")
    pollution_trends = {
        "labels": [str(item["date"]) for item in pollution_qs],
        "data": [round(item["avg_pollution"], 2) for item in pollution_qs]
    }

    # Eco-cost trends by date
    eco_qs = RouteHistory.objects.annotate(date=TruncDate("searched_at")) \
        .values("date").annotate(avg_cost=Avg("eco_cost")).order_by("date")
    eco_cost_trends = {
        "labels": [str(item["date"]) for item in eco_qs],
        "data": [round(item["avg_cost"], 2) for item in eco_qs]
    }

    # Popular routes
    popular_qs = RouteHistory.objects.values("source", "destination") \
        .annotate(total=Count("id")).order_by("-total")[:5]
    popular_routes = {
        "labels": [f"{r['source']} → {r['destination']}" for r in popular_qs],
        "data": [r["total"] for r in popular_qs]
    }

    # Active users
    active_users = list(User.objects.annotate(route_count=Count("routehistory")) \
                        .filter(route_count__gt=0).order_by("-route_count")[:5] \
                        .values("username", "route_count"))

    # Top sources and destinations
    source_stats = list(RouteHistory.objects.values("source")
                        .annotate(total=Count("id")).order_by("-total")[:5])
    destination_stats = list(RouteHistory.objects.values("destination")
                        .annotate(total=Count("id")).order_by("-total")[:5])

    context = {
        "total_users": total_users,
        "total_routes": total_routes,
        "avg_ecocost": round(avg_ecocost, 2),
        "pollution_trends": json.dumps(pollution_trends),
        "eco_cost_trends": json.dumps(eco_cost_trends),
        "popular_routes": json.dumps(popular_routes),
        "active_users": active_users,
        "source_stats": source_stats,
        "destination_stats": destination_stats,
    }
    return render(request, "adminpanel/dashboard.html", context)


# ---------------------------
# User Management
# ---------------------------
@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.order_by("-date_joined")
    return render(request, "adminpanel/manage_users.html", {"users": users})


@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        password = request.POST.get("password").strip()

        if not username or not password:
            messages.error(request, "⚠ Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "⚠ Username already exists.")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "✅ User created successfully.")
            return redirect("adminpanel:manage_users")

    return render(request, "adminpanel/add_user.html")


@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        password = request.POST.get("password", "").strip()

        if not username:
            messages.error(request, "⚠ Username cannot be empty.")
        else:
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
                update_session_auth_hash(request, user)
            user.save()
            messages.success(request, "✅ User updated successfully.")
            return redirect("adminpanel:manage_users")

    return render(request, "adminpanel/edit_user.html", {"user": user})


@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "❌ Cannot delete a superuser.")
    else:
        user.delete()
        messages.success(request, "✅ User deleted successfully.")
    return redirect("adminpanel:manage_users")


# ---------------------------
# Route Management
# ---------------------------
@login_required
@user_passes_test(is_admin)
def view_routes(request):
    routes = RouteHistory.objects.select_related("user").order_by("-searched_at")
    user_filter = request.GET.get("user", "").strip()
    source_filter = request.GET.get("source", "").strip()
    date_filter = request.GET.get("date", "").strip()

    if user_filter:
        routes = routes.filter(user__username__icontains=user_filter)
    if source_filter:
        routes = routes.filter(source__icontains=source_filter)
    if date_filter:
        routes = routes.filter(searched_at__date=date_filter)

    return render(request, "adminpanel/view_routes.html", {
        "routes": routes,
        "user_filter": user_filter,
        "source_filter": source_filter,
        "date_filter": date_filter,
    })


@login_required
@user_passes_test(is_admin)
def edit_route(request, route_id):
    route = get_object_or_404(RouteHistory, id=route_id)
    users = User.objects.all()

    if request.method == "POST":
        route.user_id = request.POST.get("user")
        route.source = request.POST.get("source")
        route.destination = request.POST.get("destination")
        route.distance_km = float(request.POST.get("distance_km") or route.distance_km)
        route.pollution_index = float(request.POST.get("pollution_index") or route.pollution_index)
        route.green_cover = float(request.POST.get("green_cover") or route.green_cover)
        route.eco_cost = float(request.POST.get("eco_cost") or route.eco_cost)
        route.save()
        messages.success(request, "✅ Route updated successfully.")
        return redirect("adminpanel:view_routes")

    return render(request, "adminpanel/edit_route.html", {"route": route, "users": users})


@login_required
@user_passes_test(is_admin)
def delete_route(request, route_id):
    route = get_object_or_404(RouteHistory, id=route_id)
    route.delete()
    messages.success(request, "✅ Route deleted successfully.")
    return redirect("adminpanel:view_routes")
