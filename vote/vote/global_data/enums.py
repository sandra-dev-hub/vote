from django.db import models


class Role(models.TextChoices):
    ADMIN    = "ADMIN",    "Administrateur"
    ELECTEUR = "ELECTEUR", "Électeur"
    CANDIDAT = "CANDIDAT", "Candidat"


class StatutScrutin(models.TextChoices):
    OUVERT  = "ouvert",  "Ouvert"    # Période 1 : dépôt candidatures & demandes électeur
    EN_VOTE = "en_vote", "En vote"   # Période 2 : vote actif
    FERME   = "ferme",   "Fermé"     # Scrutin terminé
    ANNULE  = "annule",  "Annulé"    # Scrutin annulé


class StatutDemande(models.TextChoices):
    EN_ATTENTE = "en_attente", "En attente"
    APPROUVE   = "approuve",   "Approuvé"
    REJETE     = "rejete",     "Rejeté"