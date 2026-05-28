from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from vote.global_data.enums import StatutScrutin
from vote.users.models import Electeur
from vote.users.models import Scrutin


@shared_task
def notify_eligible_electors_for_started_scrutins():
    now = timezone.now()
    scrutins = Scrutin.objects.filter(
        statut=StatutScrutin.OUVERT,
        date_debut__lte=now,
        date_fin__gte=now,
    )

    for scrutin in scrutins:
        electeurs = Electeur.objects.select_related("demande__utilisateur").filter(
            scrutin=scrutin,
            notification_ouverture_envoyee__isnull=True,
        )
        for electeur in electeurs:
            utilisateur = electeur.demande.utilisateur
            send_mail(
                subject=f"Ouverture du scrutin: {scrutin.titre}",
                message=(
                    f"Bonjour {utilisateur.prenom or utilisateur.email},\n\n"
                    f"Le scrutin '{scrutin.titre}' est maintenant ouvert.\n"
                    "Connectez-vous pour voter avant la date de fermeture.\n\n"
                    "Merci."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[utilisateur.email],
                fail_silently=True,
            )
            electeur.notification_ouverture_envoyee = now
            electeur.save(update_fields=["notification_ouverture_envoyee", "modified"])
