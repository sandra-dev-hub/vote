from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth.views import PasswordResetView
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
    ScrutinVoteView,
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
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="pages/password_reset.html",
            email_template_name="pages/emails/password_reset_email.txt",
            subject_template_name="pages/emails/password_reset_subject.txt",
            success_url="/users/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(template_name="pages/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="pages/password_reset_confirm.html",
            success_url="/users/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(template_name="pages/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    # Dashboards
    path("admin/dashboard/", AdminDashboardView.as_view(),     name="admin_dashboard"),
    path("dashboard/",       UserDashboardView.as_view(),      name="user_dashboard"),

    # Scrutins (utilisateur)
    path("scrutins/", ScrutinUserView.as_view(),               name="scrutins"),
    path("scrutins/<slug:slug>/vote/", ScrutinVoteView.as_view(), name="scrutin_vote"),

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