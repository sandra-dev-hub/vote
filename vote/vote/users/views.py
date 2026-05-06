from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse

from vote.users.models import Utilisateur
from vote.users.forms import UserRegisterForm

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):
    model = Utilisateur
    slug_field = "id"
    slug_url_kwarg = "pk"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Utilisateur
    fields = ["matricule"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()

class UserLoginView(LoginView):
    template_name = "pages/connexion.html"
    
    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if hasattr(user, 'is_admin') and user.is_admin():
                return reverse("users:admin_dashboard")
            else:
                return reverse("users:user_dashboard")
        return super().get_success_url()
    
class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")

class UserRegisterView(SuccessMessageMixin, CreateView):
    template_name = "pages/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")
    success_message = "Votre compte a été créé avec succès ! Veuillez vous connecter."
    
user_login_view = UserLoginView.as_view()
user_logout_view = UserLogoutView.as_view()
user_register_view = UserRegisterView.as_view()

from django.views.generic import TemplateView

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/user.html"


def liste_scrutins(request):
    return TemplateView.as_view(template_name="pages/admin_dashboard/scrutin.html")(request)

def create_scrutin(request):
    return TemplateView.as_view(template_name="pages/admin_dashboard/create_scrutin.html")(request) 