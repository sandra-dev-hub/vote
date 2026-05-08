import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import (
    CreateView,
    TemplateView,
    UpdateView,
    DeleteView
)

from .forms import (
    UserRegisterForm,
    ScrutinForm,
    DemandeElecteurForm,
    DemandeCandidatureForm,
)

# ✅ FIX IMPORTANT : imports manquants
from .models import Scrutin, DemandeElecteur, DemandeCandidature


# ======================
# LOGIN
# ======================
class UserLoginView(LoginView):
    template_name = "pages/connexion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.role == "ADMIN":
            return reverse_lazy("admin_dashboard")
        return reverse_lazy("user_dashboard")


# ======================
# REGISTER
# ======================
class UserRegisterView(SuccessMessageMixin, CreateView):
    template_name = "pages/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")
    success_message = "Votre compte a été créé avec succès ! Veuillez vous connecter."


# ======================
# DASHBOARD
# ======================
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/user.html"
    login_url = "/users/login/"


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin.html"
    login_url = "/users/login/"


# ======================
# SCRUTINS ADMIN
# ======================
class ScrutinListCreateView(LoginRequiredMixin, CreateView):
    model = Scrutin
    form_class = ScrutinForm
    template_name = "pages/admin_dashboard/scrutin.html"
    success_url = reverse_lazy("liste_scrutins")

    def form_valid(self, form):
        scrutin = form.save(commit=False)
        scrutin.admin = self.request.user
        scrutin.slug = f"{slugify(scrutin.titre)}-{str(uuid.uuid4())[:8]}"
        scrutin.save()
        messages.success(self.request, "Scrutin créé avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["scrutins"] = Scrutin.objects.all().order_by("-created")
        return ctx


liste_scrutins = ScrutinListCreateView.as_view()


# ======================
# SCRUTINS UTILISATEUR
# ======================
class ScrutinUserView(TemplateView):
    template_name = "pages/scrutins.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["scrutins_ouverts"] = Scrutin.objects.filter(
            statut="ouvert"
        ).order_by("-date_debut")

        if self.request.user.is_authenticated:
            ctx["demandes_electeur_ids"] = set(
                DemandeElecteur.objects.filter(utilisateur=self.request.user)
                .values_list("scrutin_id", flat=True)
            )

            ctx["demandes_candidature_ids"] = set(
                DemandeCandidature.objects.filter(utilisateur=self.request.user)
                .values_list("scrutin_id", flat=True)
            )
        else:
            ctx["demandes_electeur_ids"] = set()
            ctx["demandes_candidature_ids"] = set()

        return ctx

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(f"{reverse('login')}?next={request.path}")

        type_demande = request.POST.get("type_demande")
        scrutin_id = request.POST.get("scrutin_id")
        commentaire = request.POST.get("commentaire", "").strip()

        try:
            scrutin = Scrutin.objects.get(pk=scrutin_id, statut="ouvert")
        except Scrutin.DoesNotExist:
            messages.error(request, "Scrutin introuvable ou fermé.")
            return self.get(request, *args, **kwargs)

        # ELECTEUR
        if type_demande == "electeur":

            if DemandeElecteur.objects.filter(
                utilisateur=request.user,
                scrutin=scrutin
            ).exists():
                messages.error(request, "Vous avez déjà soumis une demande d'électeur.")
            else:
                DemandeElecteur.objects.create(
                    utilisateur=request.user,
                    scrutin=scrutin,
                    commentaire=commentaire or None,
                )
                messages.success(request, "Demande électeur envoyée avec succès !")

        # CANDIDATURE
        elif type_demande == "candidature":

            if DemandeCandidature.objects.filter(
                utilisateur=request.user,
                scrutin=scrutin
            ).exists():
                messages.error(request, "Vous avez déjà soumis une candidature.")
            else:
                DemandeCandidature.objects.create(
                    utilisateur=request.user,
                    scrutin=scrutin,
                    commentaire=commentaire or None,
                )
                messages.success(request, "Candidature envoyée avec succès !")

        return self.get(request, *args, **kwargs)


# ======================
# UPDATE SCRUTIN
# ======================
class ScrutinUpdateView(LoginRequiredMixin, UpdateView):
    model = Scrutin
    form_class = ScrutinForm
    template_name = "pages/admin_dashboard/scrutin_edit.html"
    success_url = reverse_lazy("liste_scrutins")

    def form_valid(self, form):
        messages.success(self.request, "Scrutin modifié avec succès !")
        return super().form_valid(form)


# ======================
# DELETE SCRUTIN
# ======================
class ScrutinDeleteView(LoginRequiredMixin, DeleteView):
    model = Scrutin
    template_name = "pages/admin_dashboard/scrutin_confirm_delete.html"
    success_url = reverse_lazy("liste_scrutins")

    def form_valid(self, form):
        messages.success(self.request, "Scrutin supprimé avec succès !")
        return super().form_valid(form)


scrutin_update = ScrutinUpdateView.as_view()
scrutin_delete = ScrutinDeleteView.as_view()