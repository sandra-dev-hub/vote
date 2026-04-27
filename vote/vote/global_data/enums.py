# ennum
from django.db import models

class Role(models.TextChoices):
    ADMIN = "admin", "Administrateur"
    ELECTEUR = "electeur", "Electeur"


class StatutScrutin(models.TextChoices):
    OUVERT = "ouvert", "Ouvert"
    FERME = "ferme", "Fermé"
    ANNULE = "annule", "Annulé"


class StatutDemande(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    ACCEPTEE = "acceptee", "Acceptée"
    REFUSEE = "refusee", "Refusée"
