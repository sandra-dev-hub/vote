from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import TemplateView

from vote.users.views import (
    liste_scrutins,
    ScrutinUserView,
    UserDashboardView,
    UserLoginView,
    UserRegisterView,
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact"),
    path("fonctionnalites/", TemplateView.as_view(template_name="pages/fonctionnalites.html"), name="fonction"),

    # Pages principales
    path("scrutins/", ScrutinUserView.as_view(), name="scrutins"),
    path("user/dashboard/", UserDashboardView.as_view(), name="user_dashboard"),

    # Authentification Custom
    path("users/login/", UserLoginView.as_view(), name="login"),
    path("users/register/", UserRegisterView.as_view(), name="register"),
    path("users/logout/", LogoutView.as_view(next_page="home"), name="logout"),

    # Allauth (optionnel)
    path("users/", include("vote.users.urls", namespace="users")),

    # Admin
    path("admin/dashboard/", TemplateView.as_view(template_name="pages/admin_dashboard/admin.html"), name="admin_dashboard"),
    path("admin/scrutins/", liste_scrutins, name="liste_scrutins"),

    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns