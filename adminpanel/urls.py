# adminpanel/urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "adminpanel"

urlpatterns = [
    # 🔑 Redirect /adminpanel/ → login
    path("", lambda request: redirect("adminpanel:admin_login")),

    # 🔐 Authentication
    path("login/", views.admin_login, name="admin_login"),
    path("logout/", views.admin_logout, name="admin_logout"),

    # 📊 Dashboard
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # 👥 User Management
    path("users/", views.manage_users, name="manage_users"),
    path("users/add/", views.add_user, name="add_user"),
    path("users/<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),

    # 🛣️ Route Management
    path("routes/", views.view_routes, name="view_routes"),
    #path("routes/add/", views.add_route, name="add_route"),
    path("routes/<int:route_id>/edit/", views.edit_route, name="edit_route"),
    path("routes/<int:route_id>/delete/", views.delete_route, name="delete_route"),
]
