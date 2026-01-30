from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),  # ✅ add profile URL
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
]
