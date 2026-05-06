from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.views import defaults as default_views

# 1. ON DEPLACE L'IMPORT ICI (AU DEBUT)
# Si ton dossier s'appelle 'users', garde 'from users import views'
# Sinon, utilise TemplateView comme tu le faisais pour les autres
# Pour rester cohérent avec ton code actuel, on va utiliser TemplateView pour le scrutin

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="pages/contact.html"), name="contact"),

    # === DASHBOARDS ===
    path("admin/dashboard/", 
     TemplateView.as_view(template_name="pages/admin_dashboard/admin.html"), 
     name="admin_dashboard"),
    
    path("admin/candidat/", 
         TemplateView.as_view(template_name="pages/admin_candidat.html"), 
         name="admin_candidat"),

    # NOUVELLE ROUTE POUR LE SCRUTIN
    path("admin/scrutins/", 
         TemplateView.as_view(template_name="pages/admin_dashboard/scrutin.html"), 
         name="liste_scrutins"),

    # USER DASHBOARD
    path("user/dashboard/", 
         TemplateView.as_view(template_name="pages/user_dashboard/user.html"), 
         name="user_dashboard"),

    path("users/dashboard/", 
         TemplateView.as_view(template_name="pages/user_dashboard/user.html"), 
         name="users_dashboard"),

    path("detail/candidat/", 
         TemplateView.as_view(template_name="pages/detail_candidat.html"), 
         name="detail_candidat"),
    
    path("fonctionnalites/", 
         TemplateView.as_view(template_name="pages/fonctionnalites.html"), 
         name="fonction"),
    
    path("profile/", 
         TemplateView.as_view(template_name="pages/profile.html"), 
         name="profile"),

    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='pages/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='pages/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='pages/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='pages/password_reset_complete.html'), name='password_reset_complete'),

    path(settings.ADMIN_URL, admin.site.urls),
    path("users/", include("vote.users.urls", namespace="users")),
]

# Debug Toolbar
if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)