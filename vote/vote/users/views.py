import uuid
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import (
    CreateView, TemplateView, UpdateView, DeleteView, ListView
)

from .forms import (
    UserRegisterForm,
    ScrutinForm,
    DemandeElecteurForm,
    DemandeCandidatureForm,
)
from .models import (
    Scrutin, DemandeElecteur, DemandeCandidature,
    Electeur, Candidat
)
from vote.global_data.enums import StatutDemande


# HELPERS
def envoyer_notification(utilisateur, sujet, corps):
    """Envoie un email de notification à l'utilisateur."""
    try:
        send_mail(
            subject=sujet,
            message=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=True,
        )
    except Exception:
        pass  # Ne jamais bloquer sur l'email


def get_sidebar_counts():
    """Retourne les compteurs de demandes en attente pour la sidebar."""
    return {
        "nb_demandes_electeur": DemandeElecteur.objects.filter(
            statut=StatutDemande.EN_ATTENTE
        ).count(),
        "nb_demandes_candidat": DemandeCandidature.objects.filter(
            statut=StatutDemande.EN_ATTENTE
        ).count(),
    }


# LOGIN
class UserLoginView(LoginView):
    template_name = "pages/connexion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.role == "ADMIN":
            return reverse_lazy("admin_dashboard")
        return reverse_lazy("user_dashboard")


# REGISTER
class UserRegisterView(SuccessMessageMixin, CreateView):
    template_name = "pages/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")
    success_message = "Votre compte a été créé avec succès ! Veuillez vous connecter."


# DASHBOARDS
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/user.html"
    login_url = "/users/login/"


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin.html"
    login_url = "/users/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_sidebar_counts())
        return ctx


# SCRUTINS ADMIN
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
        ctx.update(get_sidebar_counts())
        return ctx


liste_scrutins = ScrutinListCreateView.as_view()


# SCRUTINS UTILISATEUR
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
        scrutin_id   = request.POST.get("scrutin_id")
        commentaire  = request.POST.get("commentaire", "").strip()

        try:
            scrutin = Scrutin.objects.get(pk=scrutin_id, statut="ouvert")
        except Scrutin.DoesNotExist:
            messages.error(request, "Scrutin introuvable ou fermé.")
            return self.get(request, *args, **kwargs)

        if type_demande == "electeur":
            if DemandeElecteur.objects.filter(
                utilisateur=request.user, scrutin=scrutin
            ).exists():
                messages.error(request, "Vous avez déjà soumis une demande d'électeur.")
            else:
                DemandeElecteur.objects.create(
                    utilisateur=request.user,
                    scrutin=scrutin,
                    commentaire=commentaire or None,
                )
                messages.success(request, "Demande électeur envoyée avec succès !")

        elif type_demande == "candidature":
            if DemandeCandidature.objects.filter(
                utilisateur=request.user, scrutin=scrutin
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



# UPDATE / DELETE SCRUTIN
class ScrutinUpdateView(LoginRequiredMixin, UpdateView):
    model = Scrutin
    form_class = ScrutinForm
    template_name = "pages/admin_dashboard/scrutin_edit.html"
    success_url = reverse_lazy("liste_scrutins")

    def form_valid(self, form):
        messages.success(self.request, "Scrutin modifié avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_sidebar_counts())
        return ctx


class ScrutinDeleteView(LoginRequiredMixin, DeleteView):
    model = Scrutin
    template_name = "pages/admin_dashboard/scrutin_confirm_delete.html"
    success_url = reverse_lazy("liste_scrutins")

    def form_valid(self, form):
        messages.success(self.request, "Scrutin supprimé avec succès !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_sidebar_counts())
        return ctx


scrutin_update = ScrutinUpdateView.as_view()
scrutin_delete = ScrutinDeleteView.as_view()



# LISTE DEMANDES ÉLECTEURS (Admin)
class DemandesElecteursView(LoginRequiredMixin, ListView):
    """
    Affiche toutes les demandes d'inscription comme électeur.
    L'admin peut filtrer par statut via ?statut=en_attente|approuve|rejete
    """
    model = DemandeElecteur
    template_name = "pages/admin_dashboard/demandes_electeurs.html"
    context_object_name = "demandes"
    login_url = "/users/login/"

    def get_queryset(self):
        qs = DemandeElecteur.objects.select_related(
            "utilisateur", "scrutin"
        ).order_by("-date_soumission")

        statut = self.request.GET.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nb_en_attente"] = DemandeElecteur.objects.filter(statut=StatutDemande.EN_ATTENTE).count()
        ctx["nb_approuve"]   = DemandeElecteur.objects.filter(statut=StatutDemande.APPROUVE).count()
        ctx["nb_rejete"]     = DemandeElecteur.objects.filter(statut=StatutDemande.REJETE).count()
        ctx.update(get_sidebar_counts())
        return ctx


demandes_electeurs = DemandesElecteursView.as_view()


# TRAITER UNE DEMANDE ÉLECTEUR
class TraiterDemandeElecteurView(LoginRequiredMixin, View):
    """
    POST uniquement.
    action=approuver → crée l'objet Electeur + notifie l'utilisateur
    action=rejeter   → marque la demande rejetée + notifie l'utilisateur
    """
    login_url = "/users/login/"

    @transaction.atomic
    def post(self, request, pk):
        demande = get_object_or_404(DemandeElecteur, pk=pk)
        action  = request.POST.get("action")

        if demande.statut != StatutDemande.EN_ATTENTE:
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect("users:demandes_electeurs")

        if action == "approuver":
            # 1. Mettre à jour la demande
            demande.statut = StatutDemande.APPROUVE
            demande.date_traitement = timezone.now()
            demande.save()

            # 2. Créer l'électeur
            Electeur.objects.get_or_create(
                demande=demande,
                defaults={"scrutin": demande.scrutin}
            )
            # 3. Notifier l'utilisateur
            envoyer_notification(
                demande.utilisateur,
                sujet="✅ Votre demande d'électeur a été approuvée — ICAB",
                corps=(
                    f"Bonjour {demande.utilisateur.prenom or demande.utilisateur.email},\n\n"
                    f"Votre demande d'inscription comme électeur pour le scrutin "
                    f"« {demande.scrutin.titre} » a été APPROUVÉE.\n\n"
                    f"Vous pouvez dès maintenant vous connecter à la plateforme et voter.\n\n"
                    f"Bonne élection !\n\nL'équipe ICAB Bafoussam"
                ),
            )

            messages.success(
                request,
                f"✅ Demande de {demande.utilisateur.email} approuvée. "
                f"L'utilisateur est maintenant électeur."
            )

        elif action == "rejeter":
            demande.statut = StatutDemande.REJETE
            demande.date_traitement = timezone.now()
            demande.save()

            envoyer_notification(
                demande.utilisateur,
                sujet="❌ Votre demande d'électeur a été refusée — ICAB",
                corps=(
                    f"Bonjour {demande.utilisateur.prenom or demande.utilisateur.email},\n\n"
                    f"Nous avons le regret de vous informer que votre demande d'inscription "
                    f"comme électeur pour le scrutin « {demande.scrutin.titre} » "
                    f"n'a pas pu être acceptée.\n\n"
                    f"Pour plus d'informations, contactez l'administration.\n\n"
                    f"L'équipe ICAB Bafoussam"
                ),
            )

            messages.warning(
                request,
                f"❌ Demande de {demande.utilisateur.email} rejetée."
            )

        return redirect("users:demandes_electeurs")


traiter_demande_electeur = TraiterDemandeElecteurView.as_view()


# LISTE DEMANDES CANDIDATURES (Admin)
class DemandesCandidaturesView(LoginRequiredMixin, ListView):
    """
    Affiche toutes les demandes de candidature.
    """
    model = DemandeCandidature
    template_name = "pages/admin_dashboard/demandes_candidatures.html"
    context_object_name = "demandes"
    login_url = "/users/login/"

    def get_queryset(self):
        qs = DemandeCandidature.objects.select_related(
            "utilisateur", "scrutin"
        ).order_by("-date_soumission")

        statut = self.request.GET.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nb_en_attente"] = DemandeCandidature.objects.filter(statut=StatutDemande.EN_ATTENTE).count()
        ctx["nb_approuve"]   = DemandeCandidature.objects.filter(statut=StatutDemande.APPROUVE).count()
        ctx["nb_rejete"]     = DemandeCandidature.objects.filter(statut=StatutDemande.REJETE).count()
        ctx.update(get_sidebar_counts())
        return ctx


demandes_candidatures = DemandesCandidaturesView.as_view()


# TRAITER UNE DEMANDE CANDIDATURE
class TraiterDemandeCandidatureView(LoginRequiredMixin, View):
    """
    POST uniquement.
    action=approuver → crée l'objet Candidat + notifie l'utilisateur
    action=rejeter   → marque rejetée + notifie l'utilisateur
    """
    login_url = "/users/login/"

    @transaction.atomic
    def post(self, request, pk):
        demande = get_object_or_404(DemandeCandidature, pk=pk)
        action  = request.POST.get("action")

        if demande.statut != StatutDemande.EN_ATTENTE:
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect("users:demandes_candidatures")

        if action == "approuver":
            demande.statut = StatutDemande.APPROUVE
            demande.date_traitement = timezone.now()
            demande.save()

            # Créer le candidat avec un slug unique
            slug = f"{slugify(demande.utilisateur.nom or demande.utilisateur.email)}-{str(uuid.uuid4())[:8]}"
            Candidat.objects.get_or_create(
                demande=demande,
                defaults={"slug": slug, "scrutin": demande.scrutin}
            )

            envoyer_notification(
                demande.utilisateur,
                sujet="🎉 Votre candidature a été approuvée — ICAB",
                corps=(
                    f"Bonjour {demande.utilisateur.prenom or demande.utilisateur.email},\n\n"
                    f"Félicitations ! Votre candidature pour le scrutin "
                    f"« {demande.scrutin.titre} » a été APPROUVÉE.\n\n"
                    f"Votre profil de candidat est maintenant visible sur la plateforme. "
                    f"Bonne chance pour la suite !\n\n"
                    f"L'équipe ICAB Bafoussam"
                ),
            )

            messages.success(
                request,
                f"🎉 Candidature de {demande.utilisateur.email} approuvée. "
                f"Le candidat est maintenant actif."
            )

        elif action == "rejeter":
            demande.statut = StatutDemande.REJETE
            demande.date_traitement = timezone.now()
            demande.save()

            envoyer_notification(
                demande.utilisateur,
                sujet="❌ Votre candidature n'a pas été retenue — ICAB",
                corps=(
                    f"Bonjour {demande.utilisateur.prenom or demande.utilisateur.email},\n\n"
                    f"Nous avons le regret de vous informer que votre candidature "
                    f"pour le scrutin « {demande.scrutin.titre} » n'a pas été retenue.\n\n"
                    f"Nous vous remercions de votre intérêt et vous encourageons "
                    f"à participer aux prochaines élections.\n\n"
                    f"L'équipe ICAB Bafoussam"
                ),
            )

            messages.warning(
                request,
                f"❌ Candidature de {demande.utilisateur.email} rejetée."
            )

        return redirect("users:demandes_candidatures")


traiter_demande_candidature = TraiterDemandeCandidatureView.as_view()