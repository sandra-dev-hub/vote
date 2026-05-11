from django.db import models


class Role(models.TextChoices):
    ADMIN    = "ADMIN",    "Administrateur"
    ELECTEUR = "ELECTEUR", "Électeur"
    CANDIDAT = "CANDIDAT", "Candidat"


class StatutScrutin(models.TextChoices):
    OUVERT = "ouvert", "Ouvert"
    FERME  = "ferme",  "Fermé"
    ANNULE = "en attente", "En attente"


class StatutDemande(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    APPROUVE   = "approuve",   "Approuvé"
    REJETE     = "rejete",     "Rejeté"