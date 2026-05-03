from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView


# c'est pour le 1,2,3,4
from django.contrib.auth import views as auth_views 

from django.contrib import admin
from django.urls import path

# === IMPORT DES VUES PERSONNALISÉES ===
from users.views import password_reset_request, password_reset_verify

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("admin/candidat/", TemplateView.as_view(template_name="pages/admin_candidat.html"), name="admin_candidat"),
    path("admin/dashboard/", TemplateView.as_view(template_name="pages/admin_dashboard.html"), name="admin_dashboard"),
    path("connexion/", TemplateView.as_view(template_name="pages/connexion.html"), name="connexion"),
    path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact"),
    path("detail/candidat/", TemplateView.as_view(template_name="pages/detail_candidat.html"), name="detail_candidat"),
    path("fonctionnalites/", TemplateView.as_view(template_name="pages/fonctionnalites.html"), name="fonction"),
    path("profile/", TemplateView.as_view(template_name="pages/profile.html"), name="profile"),
    path("register/", TemplateView.as_view(template_name="pages/register.html"), name="register"),

    path('admin/', admin.site.urls),
    
    # Authentification
    path('connexion/', include('django.contrib.auth.urls')),   # Optionnel si tu utilises les vues par défaut
    
    # Tes nouvelles vues pour la réinitialisation par code
    path('password_reset/', password_reset_request, name='password_reset_request'),
    path('password_reset/verify/', password_reset_verify, name='password_reset_verify'),

# 1. Formulaire (envoi email)
path(
    'password_reset/',
    auth_views.PasswordResetView.as_view(
        template_name='pages/password_reset.html'
    ),
    name='password_reset'
),

# 2. Page "lien envoyé"
path(
    'password_reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='pages/password_reset_done.html'
    ),
    name='password_reset_done'
),

# 3. Lien reçu par email
path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='pages/password_reset_confirm.html'
    ),
    name='password_reset_confirm'
),

# 4. Succès final
path(
    'reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='pages/password_reset_complete.html'
    ),
    name='password_reset_complete'
),


    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("vote.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    # ...
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
