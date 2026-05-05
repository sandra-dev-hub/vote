import uuid

from django.contrib.auth.models import AbstractUser
# from django.db.models import CharField
# from django.urls import reverse
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth.hashers import make_password
from django.db import models
from django_extensions.db.models import ActivatorModel
from django_extensions.db.models import TimeStampedModel
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from vote.global_data.enums import Role, StatutDemande, StatutScrutin
from vote.users.managers import UserManager

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class BaseModel(TimeStampedModel, ActivatorModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True



class Utilisateur(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Modèle utilisateur global du système.
    Aucun rôle métier ici (électeur/candidat = contextuel via scrutin).
    """

    email = models.EmailField(unique=True)
    matricule = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ELECTEUR)


    is_verified = models.BooleanField(default=False)

    # permissions système (admin technique uniquement)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    # timestamps et UUID viennent de BaseModel

    class Meta:
        db_table = "utilisateurs"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["matricule"]),
        ]



    # -----------------------------
    # 🧠 HELPERS MÉTIER
    # -----------------------------
    def is_admin(self) -> bool:
        return self.is_staff or self.is_superuser or self.role == Role.ADMIN


    def __str__(self):
        return f"{self.email} ({self.matricule})"
    
class Administrateur(Utilisateur):
    nom_admin = models.CharField(max_length=100, verbose_name="Nom de l'administrateur")
    prenom_admin = models.CharField(max_length=100, verbose_name="Prénom de l'administrateur")
    telephone = models.CharField(max_length=20)

    def creer_scrutin(self):
        pass

    def publier_resultat(self):
        pass
    
    class Meta:
        managed = True
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'


class Electeur(BaseModel):
    matricule = models.CharField(max_length=50, unique=True)
    filiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)
    nom_elec = models.CharField(max_length=100, verbose_name="Nom de l'électeur")
    prenom_elec = models.CharField(max_length=100, verbose_name="Prénom de l'électeur")
    date_inscription = models.DateTimeField(auto_now_add=True)
    a_deja_vote = models.BooleanField(default=False)

    def voter(self):
        pass

    def consulter_scrutin(self):
        pass
    class Meta:
        managed = True
        verbose_name = 'Electeur'
        verbose_name_plural = 'Electeurs'


class Scrutin(BaseModel):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=50, choices=StatutScrutin.choices, default=StatutScrutin.OUVERT)
    slug = models.SlugField(unique=True)
    admin = models.ForeignKey(Administrateur, on_delete=models.CASCADE, related_name="scrutins")

    def ouvrir(self):
        pass

    def annuler(self):
        pass

    def cloturer(self):
        pass
    class Meta:
        managed = True
        verbose_name = 'Scrutin'
        verbose_name_plural = 'Scrutins'


class Candidat(BaseModel):
    nom = models.CharField(max_length=100, verbose_name="Nom du candidat")
    prenom = models.CharField(max_length=100, verbose_name="Prénom du candidat")
    description = models.TextField()
    photo = models.ImageField(upload_to="candidats/", null=True, blank=True)
    matricule = models.CharField(max_length=50)
    filiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)
    nb_vote = models.IntegerField(default=0)
    slug = models.SlugField(unique=True)
    scrutin = models.ForeignKey(Scrutin, on_delete=models.CASCADE, related_name="candidats")

    def get_pourcentage(self):
        pass
    class Meta:
        managed = True
        verbose_name = 'Candidat'
        verbose_name_plural = 'Candidats'


class Vote(BaseModel):
    horodatage = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField()
    electeur = models.ForeignKey(Electeur, on_delete=models.CASCADE, related_name="votes")
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="votes")
    scrutin = models.ForeignKey(Scrutin, on_delete=models.CASCADE, related_name="votes")

    def valider(self):
        pass
    class Meta:
        managed = True
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'


class DemandeCandidature(BaseModel):
    biographie = models.TextField()
    photo = models.ImageField(upload_to="demandes/", null=True, blank=True)
    age = models.IntegerField()
    matricule = models.CharField(max_length=50)
    filiere = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)
    statut = models.CharField(max_length=50, choices=StatutDemande.choices, default=StatutDemande.EN_ATTENTE)
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(null=True, blank=True)
    scrutin = models.ForeignKey(Scrutin, on_delete=models.CASCADE, related_name="demandes")
    admin = models.ForeignKey(Administrateur, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = True
        verbose_name = 'DemandeCandidature'
        verbose_name_plural = 'DemandeCandidatures'

class Logaudit(BaseModel):
    action = models.CharField(max_length=50)
    adresse_ip = models.GenericIPAddressField()
    horodatage = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(null=True, blank=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="logs")

    def get_rapport(self):
        pass
    class Meta:
        managed = True
        verbose_name = 'Logaudit'
        verbose_name_plural = 'Logaudits'

        