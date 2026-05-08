from django.urls import path, include
from django.contrib.auth.views import LogoutView
app_name = "users"

from .views import (
    UserLoginView,
    UserRegisterView,
    UserDashboardView,
    ScrutinUserView,
    liste_scrutins,
    AdminDashboardView,
    scrutin_update,
    scrutin_delete,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),

    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),

    path("dashboard/", UserDashboardView.as_view(), name="user_dashboard"),

    path("scrutins/", ScrutinUserView.as_view(), name="scrutins"),

    path("admin/scrutins/", liste_scrutins, name="liste_scrutins"),

    # AJOUTER ÇA
   path(
    "admin/scrutins/<uuid:pk>/modifier/",
    scrutin_update,
    name="scrutin_update"
),

path(
    "admin/scrutins/<uuid:pk>/supprimer/",
    scrutin_delete,
    name="scrutin_delete"
),
]