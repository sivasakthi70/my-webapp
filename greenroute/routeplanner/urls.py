# routeplanner/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),

    # 🔥 use custom logout (GET safe)
    path('logout/', views.custom_logout_view, name='logout'),

    path('api/route/', views.route_api_view, name='route_api'),
]
