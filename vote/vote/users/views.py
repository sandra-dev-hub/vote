from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from vote.users.models import Utilisateur

# users/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
import random
from django.contrib.auth import get_user_model

User = get_user_model()

def password_reset_request(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        delivery_method = request.POST.get('delivery_method')

        if not identifier:
            messages.error(request, "Veuillez entrer votre identifiant étudiant.")
            return render(request, 'pages/password_reset.html')

        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec cet identifiant étudiant.")
            return render(request, 'pages/password_reset.html')

        otp = str(random.randint(100000, 999999))
        
        request.session['reset_otp'] = otp
        request.session['reset_user_id'] = user.pk
        request.session['reset_method'] = delivery_method

        if delivery_method == 'email':
            print(f"[EMAIL] Code pour {user.email or 'N/A'} : {otp}")
            messages.success(request, f"Un code a été envoyé à votre email.")
        else:
            print(f"[SMS] Code généré : {otp}")
            messages.success(request, "Un code a été envoyé par SMS.")

        return redirect('password_reset_verify')

    return render(request, 'pages/password_reset.html')


def password_reset_verify(request):
    if 'reset_otp' not in request.session:
        messages.error(request, "Session expirée. Veuillez recommencer.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        
        if entered_otp == request.session.get('reset_otp'):
            request.session['reset_user_pk'] = request.session.pop('reset_user_id')
            del request.session['reset_otp']
            messages.success(request, "Code vérifié avec succès !")
            return redirect('password_reset_confirm')
        else:
            messages.error(request, "Code incorrect. Veuillez réessayer.")

    return render(request, 'pages/password_reset_done.html')

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):
    model = Utilisateur
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Utilisateur
    fields = ["name"]
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
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
