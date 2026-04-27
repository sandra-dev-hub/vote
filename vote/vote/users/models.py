import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# class User(AbstractUser):
#     """
#     Default custom user model for vote.
#     If adding fields that need to be filled at user signup,
#     check forms.SignupForm and forms.SocialSignupForms accordingly.
#     """

#     # First and last name do not cover name patterns around the globe
#     name = CharField(_("Name of User"), blank=True, max_length=255)
#     first_name = None  # type: ignore[assignment]
#     last_name = None  # type: ignore[assignment]

#     def get_absolute_url(self) -> str:
#         """Get URL for user's detail view.

#         Returns:
#             str: URL for user detail.

#         """
#         return reverse("users:detail", kwargs={"username": self.username})
    


from django.db import models

class BaseModel(models.Model):
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, blank=False)    

    class Meta:
        abstract = True

# ennum
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



class Utilisateur(BaseModel):
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255, help_text="Le mot de passe doit comporter au moins 8 caractères, inclure une majuscule, une minuscule, un chiffre et un caractère spécial.")
    est_actif = models.BooleanField(default=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.ELECTEUR)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    id_electeur = models.BooleanField(default=False)
    id_candidat = models.BooleanField(default=False)

    def se_connecter(self):
        pass

    def se_deconnecter(self):
        pass


class Administrateur(Utilisateur):
    nom_admin = models.CharField(max_length=100, verbose_name="Nom de l'administrateur")
    prenom_admin = models.CharField(max_length=100, verbose_name="Prénom de l'administrateur")
    telephone = models.CharField(max_length=20)

    def creer_scrutin(self):
        pass

    def publier_resultat(self):
        pass


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


class Vote(BaseModel):
    horodatage = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField()
    electeur = models.ForeignKey(Electeur, on_delete=models.CASCADE, related_name="votes")
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name="votes")
    scrutin = models.ForeignKey(Scrutin, on_delete=models.CASCADE, related_name="votes")

    def valider(self):
        pass


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


class Logaudit(BaseModel):
    action = models.CharField(max_length=50)
    adresse_ip = models.GenericIPAddressField()
    horodatage = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(null=True, blank=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="logs")

    def get_rapport(self):
        pass