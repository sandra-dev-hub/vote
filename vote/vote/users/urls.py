from django.contrib.auth.views import LogoutView
from django.urls import path

app_name = "users"

from .views import (
    # Auth
    AdminSettingsView,
    UserLoginView,
    UserRegisterView,
    # Dashboards
    UserDashboardView,
    AdminDashboardView,
    # Scrutins
    ScrutinUserView,
    liste_scrutins,
    scrutin_update,
    scrutin_delete,
    # Demandes électeurs
    demandes_electeurs,
    traiter_demande_electeur,
    # Demandes candidatures
    demandes_candidatures,
    traiter_demande_candidature,
)

urlpatterns = [

    # Authentification
    path("login/",   UserLoginView.as_view(),                  name="login"),
    path("register/", UserRegisterView.as_view(),              name="register"),
    path("logout/",  LogoutView.as_view(next_page="home"),     name="logout"),

    # Dashboards
    path("admin/dashboard/", AdminDashboardView.as_view(),     name="admin_dashboard"),
    path("dashboard/",       UserDashboardView.as_view(),      name="user_dashboard"),

    # Scrutins (utilisateur)
    path("scrutins/", ScrutinUserView.as_view(),               name="scrutins"),

    # Scrutins (admin CRUD)
    path("admin/scrutins/",                         liste_scrutins,  name="liste_scrutins"),
    path("admin/scrutins/<uuid:pk>/modifier/",      scrutin_update,  name="scrutin_update"),
    path("admin/scrutins/<uuid:pk>/supprimer/",     scrutin_delete,  name="scrutin_delete"),

    # Demandes Électeurs (admin)
    path(
        "admin/electeurs/demandes/",
        demandes_electeurs,
        name="demandes_electeurs",
    ),
    path(
        "admin/electeurs/demandes/<uuid:pk>/traiter/",
        traiter_demande_electeur,
        name="traiter_demande_electeur",
    ),


    # Demandes Candidatures (admin)
    path(
        "admin/candidatures/demandes/",
        demandes_candidatures,
        name="demandes_candidatures",
    ),
    path(
        "admin/candidatures/demandes/<uuid:pk>/traiter/",
        traiter_demande_candidature,
        name="traiter_demande_candidature",
    ),
    path("admin/parametres/", AdminSettingsView.as_view(), name="admin_settings"),
]