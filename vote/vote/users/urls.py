from django.urls import path
from django.views.generic import TemplateView

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .views import user_login_view, user_logout_view, user_register_view

app_name = "users"
urlpatterns = [
    path("login/", view=user_login_view, name="login"),
    path("logout/", view=user_logout_view, name="logout"),
    path("register/", view=user_register_view, name="register"),
    path("dashboard/admin/", TemplateView.as_view(template_name="pages/dashboard/admin.html"), name="admin_dashboard"),
    path("dashboard/user/", TemplateView.as_view(template_name="pages/dashboard/user_dashboard.html"), name="user_dashboard"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<uuid:pk>/", view=user_detail_view, name="detail"),
]
