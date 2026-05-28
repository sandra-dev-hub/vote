from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from vote.users.models import Candidat
from vote.users.models import Vote


@receiver(post_save, sender=Vote)
def publish_vote_update(sender, instance, created, **kwargs):
    if not created:
        return

    scrutin = instance.candidat.scrutin
    if scrutin is None:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    candidats = (
        Candidat.objects.filter(scrutin=scrutin)
        .select_related("demande__utilisateur")
        .order_by("-nombre_vote")
    )
    payload = [
        {
            "slug": candidat.slug,
            "nom": f"{candidat.demande.utilisateur.nom or ''} {candidat.demande.utilisateur.prenom or ''}".strip(),
            "votes": candidat.nombre_vote,
        }
        for candidat in candidats
    ]

    async_to_sync(channel_layer.group_send)(
        f"scrutin_{scrutin.slug}",
        {"type": "vote_update", "payload": payload},
    )
