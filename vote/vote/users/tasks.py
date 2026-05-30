import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from vote.global_data.enums import StatutDemande, StatutScrutin

logger = logging.getLogger(__name__)


# ============================================================
# TRANSITION AUTOMATIQUE DES PÉRIODES
# ============================================================

@shared_task(name="vote.users.tasks.transition_automatique_periodes")
def transition_automatique_periodes():
    """
    Tâche périodique (Celery Beat) qui :
    - Passe les scrutins OUVERT → EN_VOTE quand date_debut_vote est atteinte
    - Passe les scrutins EN_VOTE → FERME quand date_fin_vote est dépassée
    """
    from vote.users.models import Scrutin

    now = timezone.now()

    # 1. Scrutins qui doivent passer en période de VOTE
    scrutins_a_ouvrir_vote = Scrutin.objects.filter(
        statut=StatutScrutin.OUVERT,
        date_debut_vote__lte=now,
        date_fin_vote__gte=now,
    )

    for scrutin in scrutins_a_ouvrir_vote:
        scrutin.passer_en_vote()
        logger.info("[Scrutin %s] Passage automatique en période de vote.", scrutin.titre)
        # Lancer la notification aux électeurs approuvés
        notify_ouverture_vote_pour_scrutin.delay(str(scrutin.pk))

    # 2. Scrutins dont la période de vote est terminée → FERME
    scrutins_a_fermer = Scrutin.objects.filter(
        statut=StatutScrutin.EN_VOTE,
        date_fin_vote__lt=now,
    )

    for scrutin in scrutins_a_fermer:
        scrutin.cloturer()
        logger.info("[Scrutin %s] Clôture automatique après fin du vote.", scrutin.titre)


# ============================================================
# NOTIFICATION OUVERTURE DU VOTE
# ============================================================

@shared_task(name="vote.users.tasks.notify_ouverture_vote_pour_scrutin")
def notify_ouverture_vote_pour_scrutin(scrutin_id):
    """
    Notifie tous les électeurs APPROUVÉS (objet Electeur existant)
    que la période de vote est ouverte pour le scrutin donné.
    Utilise notification_ouverture_envoyee pour ne pas envoyer deux fois.
    """
    from vote.users.models import Electeur, Scrutin

    try:
        scrutin = Scrutin.objects.get(pk=scrutin_id)
    except Scrutin.DoesNotExist:
        logger.warning("[notify_ouverture_vote] Scrutin %s introuvable.", scrutin_id)
        return

    now = timezone.now()
    electeurs = (
        Electeur.objects
        .select_related("demande__utilisateur")
        .filter(
            scrutin=scrutin,
            notification_ouverture_envoyee__isnull=True,
        )
    )

    updated = []
    for electeur in electeurs.iterator(chunk_size=100):
        utilisateur = electeur.demande.utilisateur
        try:
            send_mail(
                subject=f"🗳️ Le vote est ouvert : {scrutin.titre}",
                message=(
                    f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
                    f"La période de vote pour le scrutin « {scrutin.titre} » est maintenant ouverte.\n"
                    f"Connectez-vous pour voter avant le {scrutin.date_fin_vote.strftime('%d/%m/%Y à %H:%M')}.\n\n"
                    "Merci de votre participation.\n\nL'équipe ICAB Bafoussam"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[utilisateur.email],
                fail_silently=False,
            )
            electeur.notification_ouverture_envoyee = now
            updated.append(electeur)
            logger.info("[notify_ouverture_vote] Email envoyé à %s.", utilisateur.email)
        except Exception as exc:
            logger.error(
                "[notify_ouverture_vote] Échec envoi email à %s : %s",
                utilisateur.email, exc
            )
            continue

    if updated:
        Electeur.objects.bulk_update(updated, ["notification_ouverture_envoyee"])
        logger.info(
            "[notify_ouverture_vote] %d électeurs notifiés pour le scrutin '%s'.",
            len(updated), scrutin.titre
        )


# ============================================================
# NOTIFICATION STATUT DEMANDE ÉLECTEUR
# ============================================================

@shared_task(name="vote.users.tasks.notify_electeur_statut_demande")
def notify_electeur_statut_demande(demande_id):
    """
    Notifie un utilisateur du statut de sa demande d'électeur
    (APPROUVÉ ou REJETÉ).
    """
    from vote.users.models import DemandeElecteur

    try:
        demande = DemandeElecteur.objects.select_related(
            "utilisateur", "scrutin"
        ).get(pk=demande_id)
    except DemandeElecteur.DoesNotExist:
        logger.warning("[notify_electeur_statut] DemandeElecteur %s introuvable.", demande_id)
        return

    utilisateur = demande.utilisateur
    scrutin = demande.scrutin

    if demande.statut == StatutDemande.APPROUVE:
        sujet = "✅ Votre demande d'électeur a été approuvée — ICAB"
        message = (
            f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
            f"Votre demande d'inscription comme électeur pour le scrutin "
            f"« {scrutin.titre} » a été APPROUVÉE.\n\n"
            "Vous recevrez un email dès que la période de vote sera ouverte.\n\n"
            "Bonne élection !\n\nL'équipe ICAB Bafoussam"
        )
    elif demande.statut == StatutDemande.REJETE:
        sujet = "❌ Votre demande d'électeur a été refusée — ICAB"
        message = (
            f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
            f"Votre demande d'inscription comme électeur pour le scrutin "
            f"« {scrutin.titre} » n'a pas été acceptée.\n\n"
            "L'équipe ICAB Bafoussam"
        )
    else:
        return  # Statut non concerné

    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=False,
        )
        logger.info(
            "[notify_electeur_statut] Email '%s' envoyé à %s.",
            demande.statut, utilisateur.email
        )
    except Exception as exc:
        logger.error(
            "[notify_electeur_statut] Échec envoi à %s : %s",
            utilisateur.email, exc
        )


# ============================================================
# NOTIFICATION STATUT DEMANDE CANDIDATURE
# ============================================================

@shared_task(name="vote.users.tasks.notify_candidat_statut_demande")
def notify_candidat_statut_demande(demande_id):
    """
    Notifie un utilisateur du statut de sa demande de candidature
    (APPROUVÉ ou REJETÉ).
    """
    from vote.users.models import DemandeCandidature

    try:
        demande = DemandeCandidature.objects.select_related(
            "utilisateur", "scrutin"
        ).get(pk=demande_id)
    except DemandeCandidature.DoesNotExist:
        logger.warning("[notify_candidat_statut] DemandeCandidature %s introuvable.", demande_id)
        return

    utilisateur = demande.utilisateur
    scrutin = demande.scrutin

    if demande.statut == StatutDemande.APPROUVE:
        sujet = "🎉 Votre candidature a été approuvée — ICAB"
        message = (
            f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
            f"Félicitations ! Votre candidature pour le scrutin "
            f"« {scrutin.titre} » a été APPROUVÉE.\n\n"
            "Votre profil sera visible par les électeurs dès l'ouverture du vote.\n\n"
            "Bonne chance !\n\nL'équipe ICAB Bafoussam"
        )
    elif demande.statut == StatutDemande.REJETE:
        sujet = "❌ Votre candidature n'a pas été retenue — ICAB"
        message = (
            f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
            f"Votre candidature pour le scrutin « {scrutin.titre} » "
            "n'a pas été retenue.\n\nL'équipe ICAB Bafoussam"
        )
    else:
        return  # Statut non concerné

    try:
        send_mail(
            subject=sujet,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=False,
        )
        logger.info(
            "[notify_candidat_statut] Email '%s' envoyé à %s.",
            demande.statut, utilisateur.email
        )
    except Exception as exc:
        logger.error(
            "[notify_candidat_statut] Échec envoi à %s : %s",
            utilisateur.email, exc
        )