import uuid
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import (
    CreateView, TemplateView, UpdateView, DeleteView, ListView
)

from django.views.generic import TemplateView
from .models import Candidat, Electeur, DemandeCandidature, DemandeElecteur, Vote
from .tasks import (
    notify_electeur_statut_demande,
    notify_candidat_statut_demande,
)

from .forms import (
    UserRegisterForm,
    ScrutinForm,
    DemandeElecteurForm,
    DemandeCandidatureForm,
)
from .models import (
    Scrutin,
    DemandeElecteur,
    DemandeCandidature,
    Electeur,
    Candidat
)
from vote.global_data.enums import StatutDemande, StatutScrutin


# ====================== HELPERS ======================
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


# ====================== AUTH ======================
class UserLoginView(LoginView):
    template_name = "pages/connexion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.role == "ADMIN":
            return reverse_lazy("admin_dashboard")
        return reverse_lazy("user_dashboard")


class UserRegisterView(SuccessMessageMixin, CreateView):
    template_name = "pages/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("login")
    success_message = "Votre compte a été créé avec succès ! Veuillez vous connecter."


# ====================== DASHBOARDS ======================
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/user.html"
    login_url = "/users/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        scrutins_accessibles = (
            Scrutin.objects.filter(
                statut="ouvert",
                date_debut__lte=now,
                date_fin__gte=now,
                electeurs__demande__utilisateur=self.request.user,
            )
            .distinct()
            .order_by("date_fin")
        )
        ctx["scrutins_accessibles"] = scrutins_accessibles
        return ctx


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/admin.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        ctx['today'] = timezone.now()
        
        # Statistiques
        ctx['total_candidats'] = Candidat.objects.count()
        ctx['candidats_valides'] = Candidat.objects.filter(demande__statut='approuve').count()
        ctx['candidats_en_attente'] = DemandeCandidature.objects.filter(statut='en_attente').count()
        ctx['total_electeurs'] = Electeur.objects.count()
        
        ctx['derniers_candidats'] = Candidat.objects.select_related(
            'demande__utilisateur', 'scrutin'
        ).order_by('-created')[:6]

        now = timezone.now()
        scrutin_live = (
            Scrutin.objects.filter(
                statut="ouvert",
                date_debut__lte=now,
                date_fin__gte=now,
            )
            .order_by("date_fin")
            .first()
        )
        ctx["scrutin_live"] = scrutin_live
        if scrutin_live:
            ctx["scrutin_live_resultats"] = list(
                Candidat.objects.filter(scrutin=scrutin_live)
                .select_related("demande__utilisateur")
                .order_by("-nombre_vote")
                .values(
                    "slug",
                    "nombre_vote",
                    "demande__utilisateur__nom",
                    "demande__utilisateur__prenom",
                )
            )
        else:
            ctx["scrutin_live_resultats"] = []

        # Données graphiques (temporaire)
        ctx['postes_labels'] = ['Président', 'Vice-Président', 'Trésorier', 'Secrétaire']
        ctx['postes_data'] = [5, 4, 2, 3]

        ctx['evolution_labels'] = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven']
        ctx['evolution_candidats'] = [3, 7, 4, 8, 12]
        ctx['evolution_electeurs'] = [12, 18, 9, 15, 22]

        ctx.update(get_sidebar_counts())
        return ctx


# ====================== SCRUTINS ADMIN ======================
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


# ====================== SCRUTINS UTILISATEUR ======================
class ScrutinUserView(TemplateView):
    template_name = "pages/scrutins.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        ctx["scrutins_ouverts"] = Scrutin.objects.filter(
            statut="ouvert",
            date_debut__lte=now,
            date_fin__gte=now,
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
            ctx["electeur_scrutin_ids"] = set(
                Electeur.objects.filter(demande__utilisateur=self.request.user).values_list("scrutin_id", flat=True)
            )
        else:
            ctx["demandes_electeur_ids"] = set()
            ctx["demandes_candidature_ids"] = set()
            ctx["electeur_scrutin_ids"] = set()
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
            scrutin = Scrutin.objects.get(pk=scrutin_id, statut__in=["ouvert", "en_vote"])
        except Scrutin.DoesNotExist:
            messages.error(request, "Scrutin introuvable.")
            return self.get(request, *args, **kwargs)

        # ── Vérification : on doit être en période 1 pour soumettre ──
        if not scrutin.est_periode_candidature():
            messages.error(
                request,
                "La période de dépôt des candidatures et des demandes d'électeur est terminée. "
                "Aucune nouvelle soumission n'est acceptée."
            )
            return self.get(request, *args, **kwargs)

        if type_demande == "electeur":
            if DemandeElecteur.objects.filter(utilisateur=request.user, scrutin=scrutin).exists():
                messages.error(request, "Vous avez déjà soumis une demande d'électeur.")
            else:
                DemandeElecteur.objects.create(
                    utilisateur=request.user,
                    scrutin=scrutin,
                    commentaire=commentaire or None,
                )
                messages.success(request, "Demande électeur envoyée avec succès !")

        elif type_demande == "candidature":
            if DemandeCandidature.objects.filter(utilisateur=request.user, scrutin=scrutin).exists():
                messages.error(request, "Vous avez déjà soumis une candidature.")
            else:
                DemandeCandidature.objects.create(
                    utilisateur=request.user,
                    scrutin=scrutin,
                    commentaire=commentaire or None,
                    programme=request.POST.get("programme", "").strip() or None,
                    slogan=request.POST.get("slogan", "").strip() or None,
                    image=request.FILES.get("image"),
                )
                messages.success(request, "Candidature envoyée avec succès !")

        return self.get(request, *args, **kwargs)


# ====================== DEMANDES ÉLECTEURS ======================
class DemandesElecteursView(LoginRequiredMixin, ListView):
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
        ctx["nb_approuve"] = DemandeElecteur.objects.filter(statut=StatutDemande.APPROUVE).count()
        ctx["nb_rejete"] = DemandeElecteur.objects.filter(statut=StatutDemande.REJETE).count()
        ctx.update(get_sidebar_counts())
        return ctx


class TraiterDemandeElecteurView(LoginRequiredMixin, View):
    login_url = "/users/login/"

    @transaction.atomic
    def post(self, request, pk):
        demande = get_object_or_404(DemandeElecteur, pk=pk)
        action = request.POST.get("action")

        if demande.statut != StatutDemande.EN_ATTENTE:
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect("users:demandes_electeurs")

        if action == "approuver":
            demande.statut = StatutDemande.APPROUVE
            demande.date_traitement = timezone.now()
            demande.save()

            Electeur.objects.get_or_create(
                demande=demande,
                defaults={"scrutin": demande.scrutin}
            )

            # Notification asynchrone via Celery
            notify_electeur_statut_demande.delay(str(demande.pk))
            messages.success(request, f"✅ Demande de {demande.utilisateur.email} approuvée.")

        elif action == "rejeter":
            demande.statut = StatutDemande.REJETE
            demande.date_traitement = timezone.now()
            demande.save()

            # Notification asynchrone via Celery
            notify_electeur_statut_demande.delay(str(demande.pk))
            messages.warning(request, f"❌ Demande de {demande.utilisateur.email} rejetée.")

        return redirect("users:demandes_electeurs")


# ====================== DEMANDES CANDIDATURES ======================
class DemandesCandidaturesView(LoginRequiredMixin, ListView):
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
        ctx["nb_approuve"] = DemandeCandidature.objects.filter(statut=StatutDemande.APPROUVE).count()
        ctx["nb_rejete"] = DemandeCandidature.objects.filter(statut=StatutDemande.REJETE).count()
        ctx.update(get_sidebar_counts())
        return ctx


# ====================== UTILISATEURS ======================
from .models import Utilisateur

class UsersListView(LoginRequiredMixin, ListView):
    model = Utilisateur
    template_name = "pages/admin_dashboard/utilisateurs.html"
    context_object_name = "utilisateurs"
    login_url = "/users/login/"
    paginate_by = 25

    def get_queryset(self):
        qs = Utilisateur.objects.all().order_by("-created")
        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nb_admin"] = Utilisateur.objects.filter(role="ADMIN").count()
        ctx["nb_candidat"] = Utilisateur.objects.filter(role="CANDIDAT").count()
        ctx["nb_electeur"] = Utilisateur.objects.filter(role="ELECTEUR").count()
        ctx.update(get_sidebar_counts())
        return ctx


class TraiterDemandeCandidatureView(LoginRequiredMixin, View):
    login_url = "/users/login/"

    @transaction.atomic
    def post(self, request, pk):
        demande = get_object_or_404(DemandeCandidature, pk=pk)
        action = request.POST.get("action")

        if demande.statut != StatutDemande.EN_ATTENTE:
            messages.error(request, "Cette demande a déjà été traitée.")
            return redirect("users:demandes_candidatures")

        if action == "approuver":
            demande.statut = StatutDemande.APPROUVE
            demande.date_traitement = timezone.now()
            demande.save()

            slug = f"{slugify(demande.utilisateur.nom or demande.utilisateur.email)}-{str(uuid.uuid4())[:8]}"
            Candidat.objects.get_or_create(
                demande=demande,
                defaults={"slug": slug, "scrutin": demande.scrutin}
            )

            # Notification asynchrone via Celery
            notify_candidat_statut_demande.delay(str(demande.pk))
            messages.success(request, f"🎉 Candidature de {demande.utilisateur.email} approuvée.")

        elif action == "rejeter":
            demande.statut = StatutDemande.REJETE
            demande.date_traitement = timezone.now()
            demande.save()

            # Notification asynchrone via Celery
            notify_candidat_statut_demande.delay(str(demande.pk))
            messages.warning(request, f"❌ Candidature de {demande.utilisateur.email} rejetée.")

        return redirect("users:demandes_candidatures")


class ScrutinVoteView(LoginRequiredMixin, TemplateView):
    template_name = "pages/vote_room.html"
    login_url = "/users/login/"

    def get_scrutin(self):
        return get_object_or_404(Scrutin, slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        scrutin = self.get_scrutin()
        ctx["scrutin"] = scrutin
        ctx["est_periode_vote"] = scrutin.est_periode_vote()
        ctx["candidats"] = Candidat.objects.filter(scrutin=scrutin).select_related("demande__utilisateur").order_by(
            "-nombre_vote",
        )

        electeur = Electeur.objects.filter(demande__utilisateur=self.request.user, scrutin=scrutin).first()
        ctx["est_electeur"] = electeur is not None
        ctx["a_vote"] = Vote.objects.filter(electeur=electeur).exists() if electeur else False
        return ctx

    def post(self, request, *args, **kwargs):
        scrutin = self.get_scrutin()

        # ── Garde de sécurité : vérifier qu'on est bien en période de vote ──
        if not scrutin.est_periode_vote():
            messages.error(
                request,
                "Le vote n'est pas encore ouvert ou la période de vote est terminée."
            )
            return redirect("users:scrutin_vote", slug=scrutin.slug)

        electeur = Electeur.objects.filter(demande__utilisateur=request.user, scrutin=scrutin).first()
        if electeur is None:
            messages.error(request, "Vous n'êtes pas inscrit comme électeur pour ce scrutin.")
            return redirect("users:scrutin_vote", slug=scrutin.slug)

        candidat = get_object_or_404(Candidat, slug=request.POST.get("candidat_slug"), scrutin=scrutin)
        if Vote.objects.filter(electeur=electeur).exists():
            messages.warning(request, "Vous avez déjà voté pour ce scrutin.")
            return redirect("users:scrutin_vote", slug=scrutin.slug)

        try:
            Vote.objects.create(
                electeur=electeur,
                candidat=candidat,
                adresse_ip=request.META.get("REMOTE_ADDR", "127.0.0.1"),
            )
            messages.success(request, "✅ Votre vote a été enregistré avec succès.")
        except ValidationError as exc:
            messages.error(request, f"Vote refusé : {exc.messages[0]}")

        return redirect("users:scrutin_vote", slug=scrutin.slug)



# ====================== URL MAPPING ======================
liste_scrutins = ScrutinListCreateView.as_view()
scrutin_update = ScrutinUpdateView.as_view()
scrutin_delete = ScrutinDeleteView.as_view()

demandes_electeurs = DemandesElecteursView.as_view()
traiter_demande_electeur = TraiterDemandeElecteurView.as_view()

demandes_candidatures = DemandesCandidaturesView.as_view()
traiter_demande_candidature = TraiterDemandeCandidatureView.as_view()


class AdminSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "pages/admin_dashboard/parametres.html"
    login_url = "/users/login/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(get_sidebar_counts())
        return ctx

    def post(self, request, *args, **kwargs):
        messages.success(request, "Paramètres enregistrés avec succès !")
        return redirect("users:admin_settings")