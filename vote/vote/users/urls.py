from django.urls import path
from django.views.generic import TemplateView
from .views import user_detail_view, user_redirect_view, user_update_view
from .views import user_login_view, user_logout_view, user_register_view

app_name = "users"

urlpatterns = [
    path("login/", user_login_view, name="login"),
    path("logout/", user_logout_view, name="logout"),
    path("register/", user_register_view, name="register"),
    
    path("dashboard/admin/", 
         TemplateView.as_view(template_name="pages/admin_dashboard/admin.html"), 
         name="admin_dashboard"),
    
    path("dashboard/user/", 
         TemplateView.as_view(template_name="pages/user_dashboard/user.html"), 
         name="user_dashboard"),
    
    path("~redirect/", user_redirect_view, name="redirect"),
    path("~update/", user_update_view, name="update"),
    path("<uuid:pk>/", user_detail_view, name="detail"),
]