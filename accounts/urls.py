from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import StyledAuthenticationForm
from .views import admin_profile, register


app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=StyledAuthenticationForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin-profile/", admin_profile, name="admin_profile"),
]
