# routeplanner/admin.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Route
from django.db.models import Avg, Count

User = get_user_model()

class CustomAdminSite(admin.AdminSite):
    site_header = "GreenRoute Admin"
    site_title = "GreenRoute Admin Portal"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_users = User.objects.count()
        total_routes = Route.objects.count()
        avg_eco_cost = Route.objects.aggregate(avg_cost=Avg('eco_cost'))['avg_cost'] or 0

        # Pollution trends (group by date)
        pollution_trends = (
            Route.objects.values("created_at__date")
            .annotate(total=Count("id"))
            .order_by("created_at__date")
        )

        # Most used routes (group by source/destination)
        popular_routes = (
            Route.objects.values("source", "destination")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        context = {
            "total_users": total_users,
            "total_routes": total_routes,
            "avg_eco_cost": round(avg_eco_cost, 2),
            "pollution_trends": list(pollution_trends),
            "popular_routes": list(popular_routes),
        }
        return render(request, "admin/dashboard.html", context)

# replace default admin with our custom admin
custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(User)
custom_admin_site.register(Route)
