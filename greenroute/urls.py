# greenroute/urls.py
from django.contrib import admin   # You can still import in case you use it later
from django.urls import path, include

urlpatterns = [
    # ❌ Removed the default Django admin
    # path("admin/", admin.site.urls),

    # ✅ Custom admin panel
    path("adminpanel/", include("adminpanel.urls")),

    # ✅ Main route planner app
    path("", include("routeplanner.urls")),
]
