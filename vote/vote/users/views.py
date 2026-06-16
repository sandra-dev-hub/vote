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
import json
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


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()

        # Cherche un scrutin actuellement ouvert ou en vote
        scrutin_live = (
            Scrutin.objects.filter(
                statut__in=["ouvert", "en_vote"],
                date_debut__lte=now,
                date_fin__gte=now,
            )
            .order_by("date_fin")
            .first()
        )

        if scrutin_live:
            candidats_qs = Candidat.objects.filter(scrutin=scrutin_live).select_related("demande__utilisateur").order_by("-nombre_vote")
            ctx["candidats"] = list(candidats_qs[:4])

            nb_electeurs = Electeur.objects.filter(scrutin=scrutin_live).count()
            nb_candidats = candidats_qs.count()
            nb_votes = Vote.objects.filter(candidat__scrutin=scrutin_live).count()

            transparence = round((nb_votes / nb_electeurs) * 100, 1) if nb_electeurs else 0

            ctx["stats"] = {
                "electeurs_inscrits": nb_electeurs,
                "candidats": nb_candidats,
                "transparence_pct": transparence,
                "securite_pct": 100,
            }
            ctx["scrutin"] = scrutin_live
        else:
            # Fallback global stats
            ctx["candidats"] = list(Candidat.objects.select_related("demande__utilisateur").order_by("-nombre_vote")[:4])
            nb_electeurs = Electeur.objects.count()
            nb_candidats = Candidat.objects.count()
            nb_votes = Vote.objects.count()
            transparence = round((nb_votes / nb_electeurs) * 100, 1) if nb_electeurs else 0
            ctx["stats"] = {
                "electeurs_inscrits": nb_electeurs,
                "candidats": nb_candidats,
                "transparence_pct": transparence,
                "securite_pct": 100,
            }

        return ctx


class CandidateDetailView(TemplateView):
    template_name = "pages/detail_profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        ctx["candidat"] = (
            Candidat.objects.select_related("demande__utilisateur", "scrutin").filter(slug=slug).first()
        )
        return ctx


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
    success_message = (
        "Votre compte a été créé avec succès ! "
        "Veuillez vous connecter."
    )

    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)

# ====================== DASHBOARDS ======================
class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/user_dashboard/user.html"
    login_url = "/users/login/"

    def get_context_data(self, **kwargs):
        from django.db.models import Count, F
        
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        
        # ==================== USER DATA ====================
        ctx['user'] = user
        
        # ==================== CANDIDAT CHECK ====================
        candidat = Candidat.objects.select_related(
            'demande__utilisateur',
            'scrutin'
        ).filter(demande__utilisateur=user).first()
        
        ctx['is_candidat'] = candidat is not None
        ctx['candidat'] = candidat
        
        # ==================== SCRUTINS ACCESSIBLES ====================
        scrutins_accessibles = (
            Scrutin.objects.filter(
                statut="ouvert",
                date_debut__lte=now,
                date_fin__gte=now,
                electeurs__demande__utilisateur=user,
            )
            .distinct()
            .order_by("date_fin")
        )
        ctx["scrutins_accessibles"] = scrutins_accessibles
        
        # ==================== STATISTIQUES CANDIDAT ====================
        if candidat:
            # Votes pour le candidat
            votes_count = candidat.nombre_vote or 0
            
            # Total électeurs
            total_electeurs = Electeur.objects.filter(
                scrutin=candidat.scrutin
            ).count()
            ctx['total_electeurs'] = total_electeurs
            
            # Progrès - calcul pour le template
            ctx['votes_progress_percentage'] = round(
                (votes_count / total_electeurs * 100) if total_electeurs > 0 else 0
            )
            
            # Ranking
            candidates_by_votes = Candidat.objects.filter(
                scrutin=candidat.scrutin
            ).order_by('-nombre_vote').values_list('id', flat=True)
            try:
                ranking = list(candidates_by_votes).index(candidat.id) + 1
                ctx['ranking'] = ranking
            except:
                ctx['ranking'] = None
            
            # Progrès (ancienne clé pour compatibilité)
            ctx['progress'] = ctx['votes_progress_percentage']
            
            # Votes par Filière
            votes_by_filiere = Vote.objects.filter(
                candidat=candidat
            ).values(
                'electeur__demande__utilisateur__filiere'
            ).annotate(count=Count('id')).order_by('-count')
            
            filiere_data = []
            for item in votes_by_filiere:
                filiere = item['electeur__demande__utilisateur__filiere'] or "Non spécifiée"
                count = item['count']
                percentage = round((count / votes_count * 100) if votes_count > 0 else 0)
                filiere_data.append((filiere, count, percentage))
            ctx['votes_by_filiere'] = filiere_data
            
            # Votes par Niveau
            votes_by_niveau = Vote.objects.filter(
                candidat=candidat
            ).values(
                'electeur__demande__utilisateur__niveau'
            ).annotate(count=Count('id')).order_by('-count')
            
            niveau_data = []
            for item in votes_by_niveau:
                niveau = item['electeur__demande__utilisateur__niveau'] or "Non spécifiée"
                count = item['count']
                percentage = round((count / votes_count * 100) if votes_count > 0 else 0)
                niveau_data.append((niveau, count, percentage))
            ctx['votes_by_niveau'] = niveau_data
            
            # Progrès des votes (par jour de la semaine)
            days_mapping = {
                'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mer',
                'Thursday': 'Jeu', 'Friday': 'Ven', 'Saturday': 'Sam',
                'Sunday': 'Dim'
            }
            
            weekly_votes = {
                'Lun': 0, 'Mar': 0, 'Mer': 0, 'Jeu': 0,
                'Ven': 0, 'Sam': 0, 'Dim': 0
            }
            
            # Requête simple pour les votes par jour
            try:
                votes_data = Vote.objects.filter(
                    candidat=candidat
                ).extra(
                    select={'day': 'DATE(created)'}
                ).values('day').annotate(count=Count('id'))
                
                for item in votes_data:
                    # Simplification: utiliser modulo pour distribuer
                    day_index = hash(str(item['day'])) % 7
                    day_names = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
                    weekly_votes[day_names[day_index]] += item['count']
            except:
                pass
            
            ctx['weekly_votes'] = weekly_votes
            
            # Pré-calculer les pourcentages pour le template
            max_weekly = max(weekly_votes.values()) if max(weekly_votes.values()) > 0 else 1
            weekly_with_percentage = {}
            for day, count in weekly_votes.items():
                percentage = round((count / max_weekly * 100)) if max_weekly > 0 else 0
                weekly_with_percentage[day] = {'count': count, 'percentage': percentage}
            ctx['weekly_votes_with_percentage'] = weekly_with_percentage
            ctx['max_weekly_votes'] = max_weekly
            ctx['vote_progress'] = 12.5  # À calculer si données historiques disponibles
        
        else:
            ctx['is_candidat'] = False
            ctx['vote_progress'] = 0
            
            # Données pour électeur
            # Compter les scrutins complétés, en cours, et à venir
            total_accessible_scrutins = Electeur.objects.filter(
                demande__utilisateur=user
            ).values('scrutin').distinct().count()
            
            completed_scrutins_count = Vote.objects.filter(
                electeur__demande__utilisateur=user
            ).values('candidat__scrutin').distinct().count()
            
            active_scrutins = Scrutin.objects.filter(
                statut="ouvert",
                date_debut__lte=now,
                date_fin__gte=now,
            ).count()
            
            upcoming_scrutins_count = Scrutin.objects.filter(
                date_debut__gt=now,
            ).count()
            
            total_scrutins = total_accessible_scrutins if total_accessible_scrutins > 0 else 1
            
            ctx['total_scrutins'] = total_scrutins
            ctx['completed_scrutins_count'] = completed_scrutins_count
            ctx['active_scrutins_count'] = active_scrutins
            ctx['upcoming_scrutins_count'] = upcoming_scrutins_count
            
            # Pré-calculer les pourcentages
            ctx['completed_scrutins_percentage'] = round((completed_scrutins_count / total_scrutins * 100)) if total_scrutins > 0 else 0
            ctx['active_scrutins_percentage'] = round((active_scrutins / total_scrutins * 100)) if total_scrutins > 0 else 0
            ctx['upcoming_scrutins_percentage'] = round((upcoming_scrutins_count / total_scrutins * 100)) if total_scrutins > 0 else 0
            
            # Participation rate
            ctx['total_accessible_scrutins'] = total_accessible_scrutins
            ctx['user_votes_count'] = completed_scrutins_count
            ctx['participation_percentage'] = round(
                (completed_scrutins_count / total_accessible_scrutins * 100) if total_accessible_scrutins > 0 else 0
            )
        
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